import streamlit as st
from transformers import pipeline
import torch
import io
import pyttsx3
import tempfile

# Load models only once (cache)
@st.cache_resource
def get_stt_pipeline():
    return pipeline("automatic-speech-recognition", model="openai/whisper-base", device=0 if torch.cuda.is_available() else -1)

def transcribe_audio(audio_bytes):
    stt = get_stt_pipeline()
    return stt(audio_bytes)["text"]

def synthesize_speech(text):
    engine = pyttsx3.init()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as fp:
        temp_wav_path = fp.name
    engine.save_to_file(text, temp_wav_path)
    engine.runAndWait()
    with open(temp_wav_path, 'rb') as f:
        audio_bytes = f.read()
    return audio_bytes 