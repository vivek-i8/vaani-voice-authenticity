from typing import List
import librosa
import numpy as np
from fastapi import HTTPException

from app.core.config import settings

class AudioValidationError(Exception):
    pass

def validate_audio_format(file_path: str) -> bool:
    try:
        librosa.load(file_path, sr=None)
        return True
    except Exception:
        return False

def validate_audio_duration(file_path: str) -> float:
    try:
        duration = librosa.get_duration(path=file_path)
        if duration < settings.min_audio_duration:
            raise AudioValidationError(f"Audio too short: {duration:.2f}s (minimum {settings.min_audio_duration}s)")
        return duration
    except Exception as e:
        if isinstance(e, AudioValidationError):
            raise
        raise AudioValidationError(f"Could not determine audio duration: {str(e)}")

def validate_batch_size(batch_size: int) -> None:
    if batch_size > settings.max_clips:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size {batch_size} exceeds maximum {settings.max_clips}"
        )

def validate_audio_duration_from_array(audio: np.ndarray, sr: int) -> float:
    try:
        duration = len(audio) / sr
        if duration < settings.min_audio_duration:
            raise AudioValidationError(f"Audio too short: {duration:.2f}s (minimum {settings.min_audio_duration}s)")
        return duration
    except Exception as e:
        if isinstance(e, AudioValidationError):
            raise
        raise AudioValidationError(f"Could not determine audio duration: {str(e)}")

def validate_audio_files(file_paths: List[str]) -> None:
    for file_path in file_paths:
        if not validate_audio_format(file_path):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_path}"
            )
        validate_audio_duration(file_path)