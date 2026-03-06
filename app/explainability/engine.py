import numpy as np
import librosa
from typing import Dict, Any, List

from app.ml.confidence import Classification

def analyze_pitch_variance(audio: np.ndarray, sr: int) -> float:
    try:
        pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
        pitch_values = []
        
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if len(pitch_values) < 2:
            return 0.0
        
        return np.std(pitch_values) / np.mean(pitch_values) if np.mean(pitch_values) > 0 else 0.0
    except:
        return 0.0

def analyze_spectral_flatness(audio: np.ndarray, sr: int) -> float:
    try:
        spectral_flatness = librosa.feature.spectral_flatness(y=audio)[0]
        return np.mean(spectral_flatness)
    except:
        return 0.0

def analyze_zero_crossing_rate(audio: np.ndarray) -> float:
    try:
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        return np.std(zcr)
    except:
        return 0.0

def generate_explanation(audio: np.ndarray, sr: int, classification: Classification, confidence: float) -> Dict[str, Any]:
    pitch_var = analyze_pitch_variance(audio, sr)
    spectral_flat = analyze_spectral_flatness(audio, sr)
    zcr_var = analyze_zero_crossing_rate(audio)
    
    if classification == Classification.AI_GENERATED:
        primary_reason = "Synthetic voice characteristics detected"
        contributing_factors = []
        confidence_explanation = "High confidence in AI detection due to"
        
        if pitch_var < 0.1:
            contributing_factors.append("Reduced pitch variation")
            confidence_explanation += " unnaturally stable pitch patterns"
        
        if spectral_flat > 0.3:
            contributing_factors.append("High spectral flatness")
            confidence_explanation += " and synthetic spectral characteristics"
        
        if zcr_var < 0.01:
            contributing_factors.append("Low zero-crossing variability")
            confidence_explanation += " with consistent waveform patterns"
        
        user_summary = "This voice sounds artificial because it lacks natural variations found in human speech."
        
    elif classification == Classification.HUMAN:
        primary_reason = "Natural human voice characteristics detected"
        contributing_factors = []
        confidence_explanation = "High confidence in human detection due to"
        
        if pitch_var > 0.2:
            contributing_factors.append("Natural pitch variation")
            confidence_explanation += " natural pitch fluctuations"
        
        if spectral_flat < 0.2:
            contributing_factors.append("Natural spectral patterns")
            confidence_explanation += " and authentic spectral characteristics"
        
        if zcr_var > 0.02:
            contributing_factors.append("Natural zero-crossing variability")
            confidence_explanation += " with variable speech patterns"
        
        user_summary = "This voice sounds natural with characteristics typical of human speech."
        
    else:
        primary_reason = "Low confidence in classification"
        contributing_factors = ["Insufficient clear indicators"]
        confidence_explanation = f"Confidence {confidence:.2f} is below threshold {0.6}"
        user_summary = "Unable to determine if this voice is human or AI-generated with sufficient confidence."
    
    return {
        "primary_reason": primary_reason,
        "contributing_factors": contributing_factors,
        "confidence_explanation": confidence_explanation,
        "user_summary": user_summary,
        "analysis_metrics": {
            "pitch_variance": pitch_var,
            "spectral_flatness": spectral_flat,
            "zero_crossing_variability": zcr_var
        }
    }