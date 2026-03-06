from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.api.schemas import (
    SingleClipResponse, 
    BatchClipResponse,
    HealthResponse
)
from app.services.single_clip import analyze_single_clip
from app.services.multi_clip import analyze_multiple_clips
from app.audio.validators import validate_batch_size
from app.ml.model_loader import get_model
from app.core.device import DEVICE

router = APIRouter()

@router.post("/analyze", response_model=SingleClipResponse, deprecated=True)
async def analyze_audio_legacy(audio: UploadFile = File(...), language: str = Form(...)):
    """
    DEPRECATED: Use /api/analyze endpoint instead.
    Legacy single clip analysis using model_loader service.
    """
    try:
        file_bytes = await audio.read()
        result = analyze_single_clip(file_bytes, language)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/analyze/batch", response_model=BatchClipResponse, deprecated=True)
async def analyze_batch_legacy(
    audio_files: List[UploadFile] = File(...),
    language: str = Form(...)
):
    try:
        validate_batch_size(len(audio_files))
        
        file_bytes_list = []
        for audio in audio_files:
            file_bytes = await audio.read()
            file_bytes_list.append(file_bytes)
        
        result = analyze_multiple_clips(file_bytes_list, language)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@router.get("/health", response_model=HealthResponse)
async def health_check():
    model = get_model()
    
    device_type = "cuda" if DEVICE.type == "cuda" else "cpu"
    
    return HealthResponse(
        status="ok" if model is not None else "model_not_loaded",
        device=device_type
    )