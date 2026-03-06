from typing import Dict, Any

from app.audio.validators import validate_audio_duration_from_array, AudioValidationError
from app.audio.preprocessing import preprocess_audio_from_bytes
from app.ml.inference import run_inference
from app.ml.confidence import get_confidence_result
from app.explainability.engine import generate_explanation
from app.llm import get_llm_service
from app.api.schemas import Explanation


def analyze_single_clip(file_bytes: bytes, language: str) -> Dict[str, Any]:
    try:
        audio, sr = preprocess_audio_from_bytes(file_bytes)
        validate_audio_duration_from_array(audio, sr)
        
        inference_result = run_inference(audio)
        confidence_result = get_confidence_result(inference_result["human_probability"])
        
        # Generate deterministic explanation
        deterministic_explanation = generate_explanation(
            audio, sr, 
            confidence_result["classification"], 
            confidence_result["confidence"]
        )
        
        # Get LLM service and generate enhanced explanation
        llm_service = get_llm_service()
        
        # Prepare structured data for LLM
        metrics = deterministic_explanation.get("analysis_metrics", {})
        structured_data = {
            "classification": confidence_result["classification"],
            "confidence": confidence_result["confidence"],
            "pitch_variance": metrics.get("pitch_variance"),
            "spectral_flatness": metrics.get("spectral_flatness"),
            "zero_crossing_variability": metrics.get("zero_crossing_variability")
        }
        
        # Generate explanation in primary language
        primary_explanation = llm_service.generate(structured_data, language)
        
        # Generate explanation in alternate language if available
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
            "classification": confidence_result["classification"],
            "confidence": confidence_result["confidence"],
            "human_probability": inference_result["human_probability"],
            "explanation": explanation.dict()
        }
        
    except AudioValidationError as e:
        raise Exception(f"Validation error: {str(e)}")
    except Exception as e:
        raise Exception(f"Processing error: {str(e)}")