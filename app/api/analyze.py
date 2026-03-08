import os
import tempfile
import shutil
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

import librosa
import numpy as np

# Import Claude + Bedrock pipeline
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
    Analyze uploaded audio file using VAANI pipeline + Claude explanation.
    """

    temp_file_path = None

    try:

        # Validate file type
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload an audio file."
            )

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f"_{file.filename}",
            dir=TEMP_UPLOADS_DIR
        ) as temp_file:

            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)
            temp_file.flush()

            logger.info(f"File saved temporarily: {temp_file_path}")

        # Load audio
        try:

            audio, sr = librosa.load(temp_file_path, sr=16000, mono=True)

            if len(audio) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Audio file is empty or corrupted."
                )

            logger.info(f"Audio loaded: {len(audio)} samples @ {sr}Hz")

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load audio file: {str(e)}"
            )

        # Run VAANI + Claude pipeline
        try:

            audio_bytes = audio.astype(np.float32).tobytes()

            result = analyze_single_clip(
                audio_bytes,
                language="en"
            )

            logger.info("Inference completed successfully")

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Inference failed: {str(e)}"
            )

        return JSONResponse(content=result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Unexpected error during analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

    finally:

        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"Temporary file deleted: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {str(e)}")


@analyze_router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "VAANI Analysis API"
    }
