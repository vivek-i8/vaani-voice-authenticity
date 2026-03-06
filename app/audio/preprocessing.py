import librosa
import numpy as np
import io
from typing import Tuple

from app.core.config import settings

def preprocess_audio(file_path: str) -> Tuple[np.ndarray, int]:
    try:
        audio, sr = librosa.load(file_path, sr=settings.sample_rate, mono=True)
        
        if len(audio) == 0:
            raise ValueError("Empty audio file")
        
        duration = len(audio) / sr
        if duration > settings.max_audio_duration:
            max_samples = int(settings.max_audio_duration * sr)
            audio = audio[:max_samples]
        
        audio = librosa.util.normalize(audio)
        
        return audio, sr
    except Exception as e:
        raise ValueError(f"Audio preprocessing failed: {str(e)}")

def preprocess_audio_from_bytes(file_bytes: bytes) -> Tuple[np.ndarray, int]:
    try:
        audio, sr = librosa.load(io.BytesIO(file_bytes), sr=settings.sample_rate, mono=True)
        
        if len(audio) == 0:
            raise ValueError("Empty audio data")
        
        duration = len(audio) / sr
        if duration > settings.max_audio_duration:
            max_samples = int(settings.max_audio_duration * sr)
            audio = audio[:max_samples]
        
        audio = librosa.util.normalize(audio)
        
        return audio, sr
    except Exception as e:
        raise ValueError(f"Audio preprocessing failed: {str(e)}")