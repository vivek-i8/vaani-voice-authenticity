import os
import tempfile
import shutil
import logging
import librosa

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

# Import our VAANI inference pipeline
from app.ml.inference import run_inference, generate_claude_explanation
from app.llm import get_llm_service
from app.llm.base import LLMService
from app.llm.mock_llm import MockLLM

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
analyze_router = APIRouter(prefix="/analyze", tags=["analyze"])

# Create temp uploads directory if it doesn't exist
TEMP_UPLOADS_DIR = "temp_uploads"
os.makedirs(TEMP_UPLOADS_DIR, exist_ok=True)

# Safe suffix extracted from the client filename (no path components)
_SAFE_SUFFIX_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")

def _safe_suffix(filename: str | None, max_len: int = 32) -> str:
    """Derive a path-safe temp file suffix from the client-supplied filename."""
    name = os.path.basename(filename or "")
    cleaned = "".join(c for c in name if c in _SAFE_SUFFIX_CHARS)
    return f"_{cleaned[:max_len]}" if cleaned else ".wav"

def _fallback_explanation(label: str) -> dict:
    """Structured fallback explanation preserved from V1."""
    if label == "AI":
        return {
            "summary": "Synthetic voice patterns detected with artificial characteristics.",
            "technical_analysis": "The model detected stable pitch patterns and low spectral variability common in AI-generated speech.",
            "recommendation": "Treat this voice call with caution and verify the speaker through another channel.",
            "model": "fallback",
        }
    if label == "Human":
        return {
            "summary": "Detected natural pitch variations and spectral patterns consistent with authentic human speech.",
            "technical_analysis": "Natural pitch variations and spectral patterns are consistent with authentic human speech.",
            "recommendation": "No further action required. This appears to be a genuine human voice.",
            "model": "fallback",
        }
    return {
        "summary": "Audio quality is insufficient for definitive analysis.",
        "technical_analysis": "Background noise or poor audio quality prevents accurate acoustic analysis.",
        "recommendation": "Please provide a clearer audio sample with minimal background noise.",
        "model": "fallback",
    }

@analyze_router.post("/")
async def analyze_audio_file(file: UploadFile = File(...)):
    """
    Analyze uploaded audio file using VAANI inference pipeline.
    
    Args:
        file: Uploaded audio file (WAV, MP3, etc.)
    
    Returns:
        JSON response with analysis results
    """
    temp_file_path = None
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Please upload an audio file."
            )
        
        # Create temporary file with a path-safe suffix
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=_safe_suffix(file.filename),
            dir=TEMP_UPLOADS_DIR
        ) as temp_file:
            temp_file_path = temp_file.name
            
            # Write uploaded file to temporary location
            shutil.copyfileobj(file.file, temp_file)
            temp_file.flush()
            
            logger.info(f"File saved temporarily: {temp_file_path}")
        
        # Load audio file for inference
        try:
            # Load audio with librosa (automatically handles resampling to 16kHz)
            audio, sr = librosa.load(temp_file_path, sr=16000, mono=True)
            
            # Ensure audio is not empty
            if len(audio) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Audio file is empty or corrupted."
                )
            
            logger.info(f"Audio loaded: {len(audio)} samples at {sr}Hz")
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load audio file: {str(e)}"
            )
        
        # Run VAANI inference
        try:
            result = run_inference(audio, sr)
            logger.info(f"Inference completed: {result['label']}")
            
            # Generate LLM explanation through the provider factory
            try:
                llm_service = get_llm_service()
                explanation = generate_claude_explanation(result, llm_service=llm_service)
                result["explanation"] = explanation
                result["explanation_source"] = (
                    "claude" if not isinstance(llm_service, MockLLM) else "mock"
                )
                logger.info(f"Explanation generated ({result['explanation_source']}): {explanation.get('summary', 'N/A')[:100]}...")
            except Exception as e:
                # Keep V1's structured fallback explanation on unexpected failure
                logger.warning(f"Explanation generation failed: {e}")
                result["explanation"] = _fallback_explanation(result["label"])
                result["explanation_source"] = "fallback"
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Inference failed: {str(e)}"
            )
        
        return JSONResponse(content=result)
        
    except HTTPException:
        # Re-raise FastAPI HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze_audio_file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    finally:
        # Clean up temporary file on every path (success and failure)
        if temp_file_path:
            try:
                os.unlink(temp_file_path)
                logger.info(f"Temporary file cleaned up: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file: {cleanup_error}")
