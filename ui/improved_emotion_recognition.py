import pandas as pd
import numpy as np
import re
from collections import Counter
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
import math
import matplotlib.pyplot as plt
import time
import seaborn as sns

# Try importing matplotlib with error handling
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    PLOTTING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import matplotlib: {e}")
    print("Visualization features will be disabled.")
    PLOTTING_AVAILABLE = False

# GPU Verification
print("="*50)
print("GPU Configuration")
print("="*50)
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    print(f"Number of GPUs: {torch.cuda.device_count()}")
    # Set default tensor type to cuda
    torch.set_default_tensor_type('torch.cuda.FloatTensor')
print("="*50)

# Check for GPU availability
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Initialize random seed
current_time = int(time.time())
torch.manual_seed(current_time)
if torch.cuda.is_available():
    torch.cuda.manual_seed(current_time)
    torch.cuda.manual_seed_all(current_time)
np.random.seed(current_time)

# Default dataset path
DEFAULT_DATASET_PATH = "data/datasets/student_emotion_dataset_80k_balanced.csv"

class CustomDataset(Dataset):
    def __init__(self, text_features, labels):
        self.text_features = text_features
        self.labels = labels
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return self.text_features[idx], self.labels[idx]

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super(PositionalEncoding, self).__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        return x + self.pe[:, :x.size(1)]

class ImprovedTransformerEmotionModel(nn.Module):
    def __init__(self, text_feature_size, num_classes=10, d_model=512, nhead=8, num_layers=4, dropout=0.2):
        super(ImprovedTransformerEmotionModel, self).__init__()
        
        # Larger embedding with layer normalization
        self.embedding = nn.Sequential(
            nn.Linear(text_feature_size, d_model),
            nn.LayerNorm(d_model),
            nn.Dropout(dropout)
        )
        
        # Enhanced positional encoding
        self.pos_encoder = PositionalEncoding(d_model, max_len=1000)
        
        # Multi-layer transformer with better configuration
        encoder_layers = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=2048,  # Increased from 512
            dropout=dropout,
            activation='gelu',  # Better than ReLU for transformers
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers)
        
        # Multi-head attention pooling
        self.attention_pool = nn.MultiheadAttention(d_model, nhead, batch_first=True)
        
        # Enhanced classifier with residual connections
        self.classifier = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, num_classes)
        )
        
        # Initialize weights properly
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
    
    def forward(self, text_features):
        # Enhanced embedding
        x = self.embedding(text_features)  # [batch_size, d_model]
        x = x.unsqueeze(1)  # [batch_size, 1, d_model]
        
        # Add positional encoding
        x = self.pos_encoder(x)
        
        # Transformer encoding
        x = self.transformer_encoder(x)
        
        # Attention pooling instead of simple squeeze
        query = x.mean(dim=1, keepdim=True)  # Global query
        attn_output, _ = self.attention_pool(query, x, x)
        x = attn_output.squeeze(1)
        
        return self.classifier(x)

class FocalLoss(nn.Module):
    def __init__(self, alpha=1, gamma=2):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
    
    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1-pt)**self.gamma * ce_loss
        return focal_loss.mean()

class LabelSmoothingCrossEntropy(nn.Module):
    def __init__(self, smoothing=0.1):
        super(LabelSmoothingCrossEntropy, self).__init__()
        self.smoothing = smoothing

    def forward(self, pred, target):
        n_classes = pred.size(1)
        one_hot = torch.zeros_like(pred).scatter(1, target.unsqueeze(1), 1)
        smooth_one_hot = one_hot * (1 - self.smoothing) + (self.smoothing / n_classes)
        log_prob = F.log_softmax(pred, dim=1)
        return (-smooth_one_hot * log_prob).sum(dim=1).mean()

class ImprovedEmotionRecognitionModel:
    def __init__(self):
        self.tfidf_vectorizer = None
        self.count_vectorizer = None
        self.label_encoder = LabelEncoder()
        self.model = None
        self.expected_emotions = [
            'anxious', 'confident', 'confused', 'curious', 'discouraged',
            'excited', 'frustrated', 'neutral', 'overwhelmed', 'satisfied'
        ]
        
        # Emotion synonyms for augmentation
        self.emotion_synonyms = {
            'anxious': ['worried', 'nervous', 'concerned', 'tense'],
            'confident': ['assured', 'certain', 'positive', 'sure'],
            'confused': ['puzzled', 'uncertain', 'unsure', 'perplexed'],
            'curious': ['interested', 'inquisitive', 'eager', 'intrigued'],
            'discouraged': ['disheartened', 'demotivated', 'disappointed', 'down'],
            'excited': ['enthusiastic', 'thrilled', 'eager', 'energized'],
            'frustrated': ['annoyed', 'irritated', 'upset', 'angry'],
            'neutral': ['calm', 'balanced', 'steady', 'composed'],
            'overwhelmed': ['stressed', 'burdened', 'swamped', 'overloaded'],
            'satisfied': ['content', 'pleased', 'happy', 'fulfilled']
        }
        
    def enhanced_text_preprocessing(self, text):
        """Advanced text cleaning and normalization"""
        if pd.isna(text):
            return ""
        
        # Convert to string and lowercase
        text = str(text).lower()
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Handle contractions
        text = re.sub(r"n't", " not", text)
        text = re.sub(r"'re", " are", text)
        text = re.sub(r"'s", " is", text)
        text = re.sub(r"'d", " would", text)
        text = re.sub(r"'ll", " will", text)
        text = re.sub(r"'t", " not", text)
        text = re.sub(r"'ve", " have", text)
        text = re.sub(r"'m", " am", text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\?\!\.\,\;\:\-\(\)]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def augment_text_data(self, text, emotion):
        """Simple text augmentation techniques"""
        augmented_texts = [text]
        
        # Simple augmentation: replace emotion words with synonyms
        if emotion in self.emotion_synonyms:
            for synonym in self.emotion_synonyms[emotion][:2]:  # Use first 2 synonyms
                augmented_text = text.replace(emotion, synonym)
                if augmented_text != text:
                    augmented_texts.append(augmented_text)
        
        return augmented_texts
    
    def enhanced_feature_preparation(self, df, fit_vectorizer=False, augment=False):
        """Enhanced feature preparation with multiple vectorizers"""
        print("Preparing enhanced features...")
        
        # Combine multiple text fields for richer representation
        current_queries = df['current_query'].fillna('')
        
        # Enhanced text cleaning
        cleaned_text = current_queries.apply(self.enhanced_text_preprocessing)
        
        # Data augmentation if requested
        if augment:
            print("Applying text augmentation...")
            augmented_texts = []
            augmented_labels = []
            
            for idx, (text, emotion) in enumerate(zip(cleaned_text, df['emotion'])):
                augmented_texts.append(text)
                augmented_labels.append(emotion)
                
                # Add augmented versions
                aug_texts = self.augment_text_data(text, emotion)
                for aug_text in aug_texts[1:]:  # Skip the original
                    augmented_texts.append(aug_text)
                    augmented_labels.append(emotion)
            
            cleaned_text = pd.Series(augmented_texts)
            df_augmented = pd.DataFrame({
                'current_query': augmented_texts,
                'emotion': augmented_labels
            })
            df = df_augmented
        
        # Multiple vectorizers for different aspects
        if fit_vectorizer:
            # TF-IDF with better parameters
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=2000,  # Increased from 1000
                stop_words='english',
                ngram_range=(1, 3),  # Increased from (1, 2)
                min_df=3,  # Reduced from 5
                max_df=0.85,  # Reduced from 0.9
                sublinear_tf=True,  # Apply sublinear scaling
                analyzer='word'
            )
            
            # Count vectorizer for different perspective
            self.count_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.9,
                use_idf=False  # No IDF weighting
            )
            
            # Fit both vectorizers
            tfidf_features = self.tfidf_vectorizer.fit_transform(cleaned_text)
            count_features = self.count_vectorizer.fit_transform(cleaned_text)
        else:
            tfidf_features = self.tfidf_vectorizer.transform(cleaned_text)
            count_features = self.count_vectorizer.transform(cleaned_text)
        
        # Combine features
        combined_features = np.hstack([
            tfidf_features.toarray(),
            count_features.toarray()
        ])
        
        # Normalize features
        combined_features = combined_features / (np.linalg.norm(combined_features, axis=1, keepdims=True) + 1e-8)
        
        print(f"Enhanced feature dimensions: {combined_features.shape[1]}")
        return combined_features
    
    def advanced_training_setup(self, model, learning_rate=0.0001):
        """Enhanced training configuration"""
        # Optimizer with better parameters
        optimizer = optim.AdamW(
            model.parameters(),
            lr=learning_rate,
            weight_decay=0.01,  # L2 regularization
            betas=(0.9, 0.999),
            eps=1e-8
        )
        
        # Cosine annealing scheduler with warm restarts
        scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
            optimizer,
            T_0=10,  # First restart after 10 epochs
            T_mult=2,  # Double the restart interval
            eta_min=1e-6
        )
        
        # Focal Loss for better handling of class imbalance
        criterion = FocalLoss(alpha=1, gamma=2)
        
        return criterion, optimizer, scheduler
    
    def plot_metrics(self, train_losses, val_losses, train_accs, val_accs, early_stop_epoch=None):
        if not PLOTTING_AVAILABLE:
            return
            
        plt.figure(figsize=(15, 5))
        
        # Plot loss
        plt.subplot(1, 3, 1)
        plt.plot(train_losses, label='Training Loss', linewidth=2)
        plt.plot(val_losses, label='Validation Loss', linewidth=2)
        if early_stop_epoch is not None:
            plt.axvline(x=early_stop_epoch, color='r', linestyle='--', label='Early Stopping')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Loss Over Time')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot accuracy
        plt.subplot(1, 3, 2)
        plt.plot(train_accs, label='Training Accuracy', linewidth=2)
        plt.plot(val_accs, label='Validation Accuracy', linewidth=2)
        if early_stop_epoch is not None:
            plt.axvline(x=early_stop_epoch, color='r', linestyle='--', label='Early Stopping')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.title('Accuracy Over Time')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot learning rate
        plt.subplot(1, 3, 3)
        plt.plot(range(len(train_losses)), [0.0001] * len(train_losses), label='Learning Rate', linewidth=2)
        plt.xlabel('Epoch')
        plt.ylabel('Learning Rate')
        plt.title('Learning Rate Schedule')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('improved_training_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()

    def comprehensive_evaluation(self, model, test_loader, device):
        """Comprehensive model evaluation"""
        model.eval()
        all_predictions = []
        all_labels = []
        all_probabilities = []
        
        with torch.no_grad():
            for text_batch, labels in test_loader:
                text_batch = text_batch.to(device)
                labels = labels.to(device)
                
                outputs = model(text_batch)
                probabilities = F.softmax(outputs, dim=1)
                _, predicted = torch.max(outputs, 1)
                
                all_predictions.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
                all_probabilities.extend(probabilities.cpu().numpy())
        
        # Calculate comprehensive metrics
        class_report = classification_report(all_labels, all_predictions, output_dict=True)
        
        # Macro and weighted averages
        macro_f1 = class_report['macro avg']['f1-score']
        weighted_f1 = class_report['weighted avg']['f1-score']
        
        # ROC-AUC for each class
        all_probabilities = np.array(all_probabilities)
        roc_auc_scores = []
        for i in range(all_probabilities.shape[1]):
            roc_auc_scores.append(roc_auc_score(
                (np.array(all_labels) == i).astype(int), 
                all_probabilities[:, i]
            ))
        
        return {
            'accuracy': class_report['accuracy'],
            'macro_f1': macro_f1,
            'weighted_f1': weighted_f1,
            'roc_auc_scores': roc_auc_scores,
            'mean_roc_auc': np.mean(roc_auc_scores),
            'class_report': class_report,
            'predictions': all_predictions,
            'labels': all_labels,
            'probabilities': all_probabilities
        }

    def train_with_cross_validation(self, df, n_splits=5, augment_data=False):
        """Train model using k-fold cross-validation with enhanced features"""
        print(f"\nStarting {n_splits}-fold cross-validation with improved model...")
        
        # Get unique student IDs and ensure proper shuffling
        student_ids = df['student_id'].unique()
        np.random.seed(current_time)
        np.random.shuffle(student_ids)
        
        # Initialize StratifiedKFold
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=current_time)
        
        # Store results
        fold_scores = []
        all_evaluations = []
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(df, df['emotion']), 1):
            print(f"\nFold {fold}/{n_splits}")
            
            # Split student IDs
            train_df = df.iloc[train_idx]
            val_df = df.iloc[val_idx]
            
            # Print label distribution
            print("\nLabel distribution in training set:")
            print(train_df['emotion'].value_counts(normalize=True))
            print("\nLabel distribution in validation set:")
            print(val_df['emotion'].value_counts(normalize=True))
            
            # Prepare features with augmentation for training
            X_train = self.enhanced_feature_preparation(train_df, fit_vectorizer=True, augment=augment_data)
            X_val = self.enhanced_feature_preparation(val_df, fit_vectorizer=False, augment=False)
            
            # Verify feature dimensions
            assert X_train.shape[1] == X_val.shape[1], "Feature dimension mismatch!"
            
            # Prepare labels
            y_train = self.label_encoder.fit_transform(train_df['emotion'])
            y_val = self.label_encoder.transform(val_df['emotion'])
            
            # Create datasets
            train_dataset = CustomDataset(
                torch.FloatTensor(X_train),
                torch.LongTensor(y_train)
            )
            val_dataset = CustomDataset(
                torch.FloatTensor(X_val),
                torch.LongTensor(y_val)
            )
            
            # Create data loaders with optimal batch size
            train_loader = DataLoader(
                train_dataset, 
                batch_size=64,  # Increased batch size
                shuffle=True,
                num_workers=0,
                pin_memory=True,
                generator=torch.Generator(device=device)
            )
            val_loader = DataLoader(
                val_dataset, 
                batch_size=64,
                num_workers=0,
                pin_memory=True
            )
            
            # Initialize improved model
            self.model = ImprovedTransformerEmotionModel(
                text_feature_size=X_train.shape[1], 
                num_classes=len(self.label_encoder.classes_),
                d_model=512,
                nhead=8,
                num_layers=4,
                dropout=0.2
            ).to(device)
            
            # Print model summary
            total_params = sum(p.numel() for p in self.model.parameters())
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            print(f"\nModel Summary:")
            print(f"Total parameters: {total_params:,}")
            print(f"Trainable parameters: {trainable_params:,}")
            
            # Advanced training setup
            criterion, optimizer, scheduler = self.advanced_training_setup(self.model)
            
            # Training loop
            best_val_acc = 0
            patience = 20  # Increased patience
            patience_counter = 0
            early_stop_epoch = None
            
            train_losses = []
            val_losses = []
            train_accs = []
            val_accs = []
            
            # Progress bar for epochs
            epoch_pbar = tqdm(range(100), desc=f'Training Fold {fold}')  # Increased max epochs
            
            for epoch in epoch_pbar:
                # Training
                self.model.train()
                train_loss = 0
                train_correct = 0
                train_total = 0
                
                # Progress bar for batches
                batch_pbar = tqdm(train_loader, desc=f'Epoch {epoch+1}', leave=False)
                
                for text_batch, labels in batch_pbar:
                    text_batch = text_batch.to(device)
                    labels = labels.to(device)
                    
                    optimizer.zero_grad()
                    outputs = self.model(text_batch)
                    loss = criterion(outputs, labels)
                    loss.backward()
                    
                    # Gradient clipping
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                    
                    optimizer.step()
                    
                    train_loss += loss.item()
                    _, predicted = torch.max(outputs.data, 1)
                    train_total += labels.size(0)
                    train_correct += (predicted == labels).sum().item()
                    
                    # Update batch progress bar
                    batch_pbar.set_postfix({
                        'loss': f'{loss.item():.4f}',
                        'acc': f'{100.0 * train_correct / train_total:.2f}%'
                    })
                
                train_loss = train_loss / len(train_loader)
                train_acc = train_correct / train_total
                
                # Validation
                self.model.eval()
                val_loss = 0
                val_correct = 0
                val_total = 0
                
                with torch.no_grad():
                    for text_batch, labels in val_loader:
                        text_batch = text_batch.to(device)
                        labels = labels.to(device)
                        
                        outputs = self.model(text_batch)
                        loss = criterion(outputs, labels)
                        
                        val_loss += loss.item()
                        _, predicted = torch.max(outputs.data, 1)
                        val_total += labels.size(0)
                        val_correct += (predicted == labels).sum().item()
                
                val_loss = val_loss / len(val_loader)
                val_acc = val_correct / val_total
                
                # Update learning rate
                scheduler.step()
                
                # Update epoch progress bar
                epoch_pbar.set_postfix({
                    'train_loss': f'{train_loss:.4f}',
                    'train_acc': f'{train_acc:.4f}',
                    'val_loss': f'{val_loss:.4f}',
                    'val_acc': f'{val_acc:.4f}',
                    'lr': f'{scheduler.get_last_lr()[0]:.6f}'
                })
                
                train_losses.append(train_loss)
                val_losses.append(val_loss)
                train_accs.append(train_acc)
                val_accs.append(val_acc)
                
                # Early stopping
                if val_acc > best_val_acc:
                    best_val_acc = val_acc
                    patience_counter = 0
                    # Save best model and training history
                    history = {
                        'train_losses': train_losses,
                        'val_losses': val_losses,
                        'train_accs': train_accs,
                        'val_accs': val_accs,
                        'fold': fold
                    }
                    torch.save({
                        'model_state_dict': self.model.state_dict(),
                        'history': history,
                        'vectorizers': {
                            'tfidf': self.tfidf_vectorizer,
                            'count': self.count_vectorizer
                        },
                        'label_encoder': self.label_encoder
                    }, f'improved_emotion_recognition_model_fold_{fold}.pth')
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    early_stop_epoch = epoch
                    print(f"\nEarly stopping at epoch {epoch}")
                    break
            
            # Comprehensive evaluation
            evaluation = self.comprehensive_evaluation(self.model, val_loader, device)
            all_evaluations.append(evaluation)
            
            # Plot metrics for this fold
            self.plot_metrics(train_losses, val_losses, train_accs, val_accs, early_stop_epoch)
            
            # Store fold results
            fold_scores.append({
                'fold': fold,
                'train_acc': train_acc,
                'val_acc': val_acc,
                'best_val_acc': best_val_acc,
                'macro_f1': evaluation['macro_f1'],
                'weighted_f1': evaluation['weighted_f1'],
                'mean_roc_auc': evaluation['mean_roc_auc']
            })
            
            print(f"\nFold {fold} Results:")
            print(f"Training Accuracy: {train_acc:.4f}")
            print(f"Validation Accuracy: {val_acc:.4f}")
            print(f"Best Validation Accuracy: {best_val_acc:.4f}")
            print(f"Macro F1: {evaluation['macro_f1']:.4f}")
            print(f"Weighted F1: {evaluation['weighted_f1']:.4f}")
            print(f"Mean ROC-AUC: {evaluation['mean_roc_auc']:.4f}")
        
        # Print overall results
        print("\n" + "="*60)
        print("CROSS-VALIDATION RESULTS SUMMARY")
        print("="*60)
        
        avg_val_acc = np.mean([score['val_acc'] for score in fold_scores])
        avg_macro_f1 = np.mean([score['macro_f1'] for score in fold_scores])
        avg_weighted_f1 = np.mean([score['weighted_f1'] for score in fold_scores])
        avg_roc_auc = np.mean([score['mean_roc_auc'] for score in fold_scores])
        
        print(f"Average Validation Accuracy: {avg_val_acc:.4f} ± {np.std([score['val_acc'] for score in fold_scores]):.4f}")
        print(f"Average Macro F1: {avg_macro_f1:.4f} ± {np.std([score['macro_f1'] for score in fold_scores]):.4f}")
        print(f"Average Weighted F1: {avg_weighted_f1:.4f} ± {np.std([score['weighted_f1'] for score in fold_scores]):.4f}")
        print(f"Average ROC-AUC: {avg_roc_auc:.4f} ± {np.std([score['mean_roc_auc'] for score in fold_scores]):.4f}")
        
        # Save overall results
        results = {
            'fold_scores': fold_scores,
            'overall_metrics': {
                'avg_val_acc': avg_val_acc,
                'avg_macro_f1': avg_macro_f1,
                'avg_weighted_f1': avg_weighted_f1,
                'avg_roc_auc': avg_roc_auc
            },
            'all_evaluations': all_evaluations
        }
        
        torch.save(results, 'improved_cross_validation_results.pth')
        
        return results

def load_data(file_path=DEFAULT_DATASET_PATH):
    """Load and prepare the dataset"""
    print(f"Loading data from {file_path}")
    df = pd.read_csv(file_path)
    print(f"Loaded {len(df)} records")
    print(f"Columns: {list(df.columns)}")
    return df

def main():
    # Load data
    df = load_data()
    
    # Initialize improved model
    model = ImprovedEmotionRecognitionModel()
    
    # Train with cross-validation
    results = model.train_with_cross_validation(df, n_splits=5, augment_data=True)
    
    print("\nTraining completed successfully!")
    print("Model files saved:")
    print("- improved_emotion_recognition_model_fold_X.pth (for each fold)")
    print("- improved_cross_validation_results.pth (overall results)")
    print("- improved_training_metrics.png (training plots)")

if __name__ == "__main__":
    main() 