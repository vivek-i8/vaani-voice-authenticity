from typing import Dict, Any
from enum import Enum

from app.core.config import settings

class Classification(Enum):
    HUMAN = "human"
    AI_GENERATED = "ai_generated"
    INCONCLUSIVE = "inconclusive"

def calculate_confidence(human_probability: float) -> float:
    confidence = abs(human_probability - 0.5) * 2
    return confidence

def classify_audio(human_probability: float) -> Classification:
    confidence = calculate_confidence(human_probability)
    
    if confidence < settings.confidence_threshold:
        return Classification.INCONCLUSIVE
    
    if human_probability >= 0.5:
        return Classification.HUMAN
    else:
        return Classification.AI_GENERATED

def get_confidence_result(human_probability: float) -> Dict[str, Any]:
    confidence = calculate_confidence(human_probability)
    classification = classify_audio(human_probability)
    
    return {
        "classification": classification.value,
        "confidence": confidence,
        "human_probability": human_probability
    }