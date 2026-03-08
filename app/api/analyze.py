import os
import tempfile
import shutil
import logging
import numpy as np
import librosa
import io

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

# Import our VAANI inference pipeline
from app.ml.inference import run_inference, generate_claude_explanation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
analyze_router = APIRouter(prefix="/analyze", tags=["analyze"])

# Create temp uploads directory if it doesn't exist
TEMP_UPLOADS_DIR = "temp_uploads"
os.makedirs(TEMP_UPLOADS_DIR, exist_ok=True)

@analyze_router.post("/")
async def analyze_audio_file(file: UploadFile = File(...)):
    """
    Analyze uploaded audio file using VAANI inference pipeline.
    
    Args:
        file: Uploaded audio file (WAV, MP3, etc.)
    
    Returns:
        JSON response with analysis results
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Please upload an audio file."
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=f"_{file.filename}", 
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
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load audio file: {str(e)}"
            )
        
        # Run VAANI inference
        try:
            result = run_inference(audio, sr)
            logger.info(f"Inference completed: {result['label']}")
            
            # Generate Claude explanation
            try:
                explanation = generate_claude_explanation(result)
                result["explanation"] = explanation
                logger.info(f"Claude explanation generated: {explanation.get('summary', 'N/A')[:100]}...")
            except Exception as e:
                logger.warning(f"Failed to generate Claude explanation: {str(e)}")
                # Fallback explanation with structured format
                if result["label"] == "AI":
                    result["explanation"] = {
                        "summary": "Synthetic voice patterns detected with artificial characteristics.",
                        "analysis": "The model detected stable pitch patterns and low spectral variability common in AI-generated speech.",
                        "recommendation": "Treat this voice call with caution and verify the speaker through another channel."
                    }
                elif result["label"] == "Human":
                    result["explanation"] = {
                        "summary": "Detected natural pitch variations and spectral patterns consistent with authentic human speech.",
                        "analysis": "Natural pitch variations and spectral patterns are consistent with authentic human speech.",
                        "recommendation": "No further action required. This appears to be a genuine human voice."
                    }
                else:
                    result["explanation"] = {
                        "summary": "Audio quality is insufficient for definitive analysis.",
                        "analysis": "Background noise or poor audio quality prevents accurate acoustic analysis.",
                        "recommendation": "Please provide a clearer audio sample with minimal background noise."
                    }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Inference failed: {str(e)}"
            )
        
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
            logger.info(f"Temporary file cleaned up: {temp_file_path}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up temporary file: {cleanup_error}")
        
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
