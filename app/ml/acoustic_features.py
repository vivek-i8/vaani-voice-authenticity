import numpy as np
import librosa
from typing import Tuple

def compute_pitch_variance(audio: np.ndarray, sample_rate: int = 16000) -> float:
    """
    Compute variance of fundamental frequency (pitch) across the audio signal.
    Higher variance indicates less stable pitch patterns.
    """
    try:
        # Extract pitch using librosa's piptrack
        pitches, magnitudes = librosa.piptrack(
            y=audio, 
            sr=sample_rate,
            threshold=0.1,
            fmin=50.0,
            fmax=400.0
        )
        
        # Get the dominant pitch at each time frame
        dominant_pitches = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:  # Valid pitch
                dominant_pitches.append(pitch)
        
        if len(dominant_pitches) == 0:
            return 0.0
            
        # Compute variance of pitch values
        pitch_variance = np.var(dominant_pitches)
        return float(pitch_variance)
        
    except Exception:
        return 0.0

def compute_spectral_centroid_drift(audio: np.ndarray, sample_rate: int = 16000) -> float:
    """
    Compute drift in spectral centroid over time.
    Higher drift indicates changing spectral characteristics.
    """
    try:
        # Compute spectral centroid over time windows
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)
        
        # Compute drift as variance of centroid values
        centroid_drift = np.var(spectral_centroids[0])  # Take first band
        return float(centroid_drift)
        
    except Exception:
        return 0.0

def compute_zcr_variance(audio: np.ndarray, sample_rate: int = 16000) -> float:
    """
    Compute variance of zero-crossing rate over time windows.
    Higher variance indicates inconsistent zero-crossing patterns.
    """
    try:
        # Compute zero-crossing rate over time windows
        zcr = librosa.feature.zero_crossing_rate(y=audio)[0]
        
        # Compute variance of ZCR values across all frames
        zcr_variance = np.var(zcr)
        return float(zcr_variance)
        
    except Exception:
        return 0.0

def extract_acoustic_features(audio: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
    """
    Extract all acoustic features for fusion classifier.
    Returns: [pitch_variance, spectral_drift, zcr_variance]
    """
    pitch_var = compute_pitch_variance(audio, sample_rate)
    spectral_drift = compute_spectral_centroid_drift(audio, sample_rate)
    zcr_var = compute_zcr_variance(audio, sample_rate)
    
    return np.array([pitch_var, spectral_drift, zcr_var])
