from typing import List, Dict, Any
from collections import Counter

from app.services.single_clip import analyze_single_clip
from app.llm import get_llm_service
from app.api.schemas import Explanation


def analyze_multiple_clips(file_bytes_list: List[bytes], language: str) -> Dict[str, Any]:
    classifications = []
    confidences = []
    human_probabilities = []
    
    for file_bytes in file_bytes_list:
        try:
            result = analyze_single_clip(file_bytes, language)
            
            if result.get("classification") != "error":
                classifications.append(result["classification"])
                confidences.append(result["confidence"])
                human_probabilities.append(result["human_probability"])
        except Exception as e:
            # Continue processing other clips
            pass
    
    if not classifications:
        raise Exception("All audio clips failed to process")
    
    weighted_score = calculate_weighted_score(human_probabilities, confidences)
    consistency_score = calculate_consistency(classifications)
    
    final_classification = classify_aggregated_result(weighted_score)
    final_confidence = calculate_aggregated_confidence(weighted_score)
    
    # Generate LLM-enhanced explanation for aggregated result
    llm_service = get_llm_service()
    
    structured_data = {
        "classification": final_classification,
        "confidence": final_confidence,
        "consistency_score": consistency_score,
        "total_clips": len(file_bytes_list),
        "successful_clips": len(classifications)
    }
    
    # Generate explanation in primary language
    primary_explanation = llm_service.generate(structured_data, language)
    
    # Generate explanation in alternate language
    alternate_language = "en" if language == "hi" else "hi"
    alternate_explanation = llm_service.generate(structured_data, alternate_language)
    
    # Create final explanation object
    explanation = Explanation(
        primary_language=language,
        text=primary_explanation["text"],
        advisory=primary_explanation["advisory"],
        alternate_language=alternate_language,
        alternate_text=alternate_explanation["text"],
        alternate_advisory=alternate_explanation["advisory"]
    )
    
    return {
        "classification": final_classification,
        "confidence": final_confidence,
        "explanation": explanation.dict()
    }


def calculate_weighted_score(human_probabilities: List[float], confidences: List[float]) -> float:
    if not confidences or sum(confidences) == 0:
        return 0.5
    
    weighted_sum = sum(hp * conf for hp, conf in zip(human_probabilities, confidences))
    return weighted_sum / sum(confidences)


def calculate_consistency(classifications: List[str]) -> float:
    if not classifications:
        return 0.0
    
    counter = Counter(classifications)
    majority_count = max(counter.values())
    return majority_count / len(classifications)


def classify_aggregated_result(weighted_score: float) -> str:
    if weighted_score >= 0.5:
        return "human"
    else:
        return "ai_generated"


def calculate_aggregated_confidence(weighted_score: float) -> float:
    return abs(weighted_score - 0.5) * 2