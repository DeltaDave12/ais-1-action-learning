import sys
import gc
import torch
import torch.nn.functional as F
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import joblib
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline

# Add model directory to sys.path if needed
sys.path.append(r'C:\Users\Acer\Desktop\AL-Emotion\models')

def run_inference(user_prompt):
    # --- Step 1: Emotion Recognition ---
    from improved_emotion_recognition import ImprovedEmotionRecognitionModel, ImprovedTransformerEmotionModel
    from progressive_emotion_training import device

    emotion_ckpt = "../models/progressive_model_stage2.pth"
    checkpoint = torch.load(emotion_ckpt, weights_only=False)
    emotion_model = ImprovedEmotionRecognitionModel()
    tfidf_features = len(checkpoint['vectorizers']['tfidf'].get_feature_names_out())
    count_features = len(checkpoint['vectorizers']['count'].get_feature_names_out())
    total_features = tfidf_features + count_features
    emotion_model.model = ImprovedTransformerEmotionModel(
        text_feature_size=total_features,
        num_classes=len(checkpoint['label_encoder'].classes_),
        d_model=512,
        nhead=8,
        num_layers=4,
        dropout=0.2
    ).to(device)
    emotion_model.model.load_state_dict(checkpoint['model_state_dict'])
    emotion_model.tfidf_vectorizer = checkpoint['vectorizers']['tfidf']
    emotion_model.count_vectorizer = checkpoint['vectorizers']['count']
    emotion_model.label_encoder = checkpoint['label_encoder']
    emotion_model.model.eval()

    demo_df = pd.DataFrame({'current_query': [user_prompt]})
    features = emotion_model.enhanced_feature_preparation(demo_df, fit_vectorizer=False, augment=False)
    input_tensor = torch.FloatTensor(features).to(device)
    with torch.no_grad():
        outputs = emotion_model.model(input_tensor)
        predicted_class = torch.argmax(outputs, dim=1).item()
    emotion = emotion_model.label_encoder.classes_[predicted_class]

    # Free memory
    del emotion_model, checkpoint, features, input_tensor, outputs
    gc.collect()
    torch.cuda.empty_cache()

    # --- Step 2: MLP Model ---
    mlp_model = joblib.load("../models/mlp_classifier.pkl")
    mlp_label_encoder = joblib.load("../models/label_encoder.pkl")
    sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

    query_embedding = sentence_model.encode([user_prompt])
    history_count_norm = 0.0
    mlp_input = np.hstack([query_embedding, [[history_count_norm]]])
    strategy_idx = mlp_model.predict(mlp_input)[0]
    strategy = mlp_label_encoder.inverse_transform([strategy_idx])[0]

    # Free memory
    del mlp_model, mlp_label_encoder, sentence_model, query_embedding, mlp_input, strategy_idx
    gc.collect()
    torch.cuda.empty_cache()

    # --- Step 3: Mistral 7B Model ---
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype="float16",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )
    mistral_model = AutoModelForCausalLM.from_pretrained(
        "../models/mistral_7b_quantized",
        device_map="cuda",  # or "cpu" if you don't have enough VRAM
        quantization_config=bnb_config
    )
    mistral_tokenizer = AutoTokenizer.from_pretrained("../models/mistral_7b_quantized")
    mistral_pipe = pipeline(
        "text-generation",
        model=mistral_model,
        tokenizer=mistral_tokenizer,
        max_new_tokens=1000,
        return_full_text=False
    )

    # Use conversational context if present
    if user_prompt.strip().startswith("User:") and "Assistant:" in user_prompt:
        mistral_prompt = (
            f"{user_prompt}\n"
            f"Emotion: {emotion}\n"
            f"Content decision: Use {strategy}\n"
            "Please provide a comprehensive answer."
        )
    else:
        mistral_prompt = (
            f"User prompt: {user_prompt}\n"
            f"Emotion: {emotion}\n"
            f"Content decision: Use {strategy}\n"
            "Please provide a comprehensive answer."
        )
    answer = mistral_pipe(mistral_prompt)[0]['generated_text']

    # Free memory
    del mistral_model, mistral_tokenizer, mistral_pipe
    gc.collect()
    torch.cuda.empty_cache()

    return {
        'emotion': emotion,
        'strategy': strategy,
        'answer': answer
    }

# Example usage (for testing):
if __name__ == "__main__":
    prompt = input("Enter your question: ")
    result = run_inference(prompt)
    print(f"\nPredicted Emotion: {result['emotion']}")
    print(f"Predicted Strategy: {result['strategy']}")
    print(f"Mistral 7B Answer: {result['answer']}") 