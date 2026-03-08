import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import shutil
import logging
import numpy as np
import librosa
import io

# Import our VAANI full pipeline service
from app.services.single_clip import analyze_single_clip

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
analyze_router = APIRouter(prefix="/analyze", tags=["analyze"])

# Create temp uploads directory if it doesn't exist
TEMP_UPLOADS_DIR = "temp_uploads"
os.makedirs(TEMP_UPLOADS_DIR, exist_ok=True)

@analyze_router.post("")
@analyze_router.post("/")
async def analyze_audio_file(file: UploadFile = File(...)):
    """
    Analyze uploaded audio file using VAANI full pipeline with Claude/Bedrock explanations.
    
    Args:
        file: Uploaded audio file (WAV, MP3, etc.)
    
    Returns:
        JSON response with analysis results including explanations
    """
    temp_file_path = None
    
    try:
        logger.info("=== Starting VAANI Analysis Pipeline ===")
        logger.info("Received audio file: %s (content-type: %s)", file.filename, file.content_type)
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('audio/'):
            logger.error("Invalid file type received: %s", file.content_type)
            return {
                "error": "Invalid file type",
                "details": "Please upload an audio file (WAV, MP3, etc.)"
            }
        
        logger.info("File type validation passed")
        
        # Create temporary file
        logger.info("Saving temporary file")
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=f"_{file.filename}", 
            dir=TEMP_UPLOADS_DIR
        ) as temp_file:
            temp_file_path = temp_file.name
            
            # Write uploaded file to temporary location
            shutil.copyfileobj(file.file, temp_file)
            temp_file.flush()
            
            logger.info("Temporary file saved: %s", temp_file_path)
        
        # Load audio file using librosa
        try:
            logger.info("Loading audio with librosa (16kHz mono)")
            # Load audio with librosa (automatically handles resampling to 16kHz)
            audio, sr = librosa.load(temp_file_path, sr=16000, mono=True)
            
            # Ensure audio is not empty
            if len(audio) == 0:
                logger.error("Audio file is empty or corrupted")
                return {
                    "error": "Audio file is empty or corrupted",
                    "details": "The uploaded audio file contains no data"
                }
            
            logger.info("Audio loaded successfully: %d samples at %dHz (%.2f seconds)", 
                       len(audio), sr, len(audio)/sr)
            
        except Exception as e:
            logger.exception("Audio loading failed")
            return {
                "error": "Failed to load audio file",
                "details": str(e)
            }
        
        # Convert audio waveform to float32 bytes
        try:
            logger.info("Converting audio waveform to float32 bytes")
            
            # Ensure audio is float32 (librosa typically returns float64)
            audio_float32 = audio.astype(np.float32)
            
            # Convert to bytes
            audio_bytes = audio_float32.tobytes()
            
            logger.info("Audio converted to bytes: %d bytes", len(audio_bytes))
            
        except Exception as e:
            logger.exception("Audio to bytes conversion failed")
            return {
                "error": "Failed to convert audio to bytes",
                "details": str(e)
            }
        
        # Run VAANI full pipeline with Claude/Bedrock explanations
        try:
            logger.info("Starting VAANI full pipeline analysis")
            logger.info("Running ML inference and generating explanations")
            
            # Run full pipeline with audio bytes
            result = analyze_single_clip(audio_bytes, language="en")
            
            logger.info("Full pipeline completed successfully")
            logger.info("Classification: %s (confidence: %.3f)", 
                       result.get('classification', 'unknown'), 
                       result.get('confidence', 0))
            logger.info("Explanation generated: %s", 
                       result.get('explanation', {}).get('text', 'No explanation'))
            
        except Exception as e:
            logger.exception("VAANI full pipeline failed")
            return {
                "error": "Full pipeline analysis failed",
                "details": str(e)
            }
        
        # Return analysis result
        logger.info("=== Analysis Pipeline Completed Successfully ===")
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception("Unexpected error in inference pipeline")
        return {
            "error": "Inference pipeline failed",
            "details": str(e)
        }
        
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info("Temporary file deleted: %s", temp_file_path)
            except Exception as e:
                logger.warning("Failed to delete temporary file %s: %s", temp_file_path, str(e))

@analyze_router.get("/health")
async def health_check():
    """
    Health check endpoint for the analyze service.
    """
    return {"status": "healthy", "service": "VAANI Analysis API"}

# Test function for development
def test_analyze_endpoint():
    """Test the analyze endpoint with a dummy file"""
    import io
    from fastapi.testclient import TestClient
    
    # Create a dummy WAV audio data (16kHz mono, 1 second)
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * 440 * t).astype(np.float32)  # 440 Hz sine wave
    
    # Convert to bytes
    dummy_content = audio_data.tobytes()
    
    print("🧪 Testing analyze endpoint...")
    print(f"📁 Would accept audio files and return VAANI analysis with Claude explanations")
    print(f"🔗 Endpoint: POST /analyze")
    print(f"🏥 Health check: GET /analyze/health")
    
    return True

if __name__ == "__main__":
    test_analyze_endpoint()
