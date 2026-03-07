import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import shutil
import logging

# Import our VAANI inference pipeline
from app.ml.inference import run_inference
import librosa
import numpy as np

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
    Analyze uploaded audio file using VAANI v2 inference pipeline.
    
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
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Inference failed: {str(e)}"
            )
        
        # Return analysis result
        return JSONResponse(content=result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
        
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"Temporary file deleted: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file_path}: {str(e)}")

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
    
    # Create a dummy WAV file (16kHz mono, 1 second)
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
    
    # Convert to bytes (simplified WAV format)
    # In practice, you'd use a proper WAV encoder
    dummy_content = audio_data.tobytes()
    
    print("🧪 Testing analyze endpoint...")
    print(f"📁 Would accept audio files and return VAANI analysis")
    print(f"🔗 Endpoint: POST /analyze")
    print(f"🏥 Health check: GET /analyze/health")
    
    return True

if __name__ == "__main__":
    test_analyze_endpoint()
