"""V2 analysis endpoint -- full multi-signal pipeline.

POST /api/analyze/ -- analyze uploaded audio file.

Pipeline:
1. Validate and preprocess audio
2. Run VAANI signal (required)
3. Run Spectra-AASIST3 signal (optional, degraded mode if unavailable)
4. Combine signals via deterministic ensemble truth table
5. Retrieve reference evidence examples
6. Generate deterministic explanation from structured evidence
7. Return typed V2 response
"""
import os
import tempfile
import logging
import numpy as np
import torch
import librosa

from app.core.device import DEVICE

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.ml.inference import run_vaani_signal, run_spectra_signal
from app.ml.ensemble import combine_signals
from app.ml.reference_index import retrieve_references
from app.ml.model_loader import get_wav2vec_model, get_feature_extractor
from app.explainability.engine import generate_explanation

logger = logging.getLogger(__name__)

analyze_router = APIRouter(prefix="/analyze", tags=["analyze"])

TEMP_UPLOADS_DIR = "temp_uploads"
os.makedirs(TEMP_UPLOADS_DIR, exist_ok=True)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
MIN_DURATION = 3.0
MAX_DURATION = 5.0
SAMPLE_RATE = 16000


@analyze_router.post("/")
async def analyze_audio_file(file: UploadFile = File(...)):
    """Analyze uploaded audio file using VAANI V2 multi-signal pipeline."""
    temp_file_path = None
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")

        # Validate file size
        file_bytes = await file.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 20MB.")
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file.")

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}", dir=TEMP_UPLOADS_DIR) as tf:
            temp_file_path = tf.name
            tf.write(file_bytes)

        # Load audio
        try:
            audio, sr = librosa.load(temp_file_path, sr=SAMPLE_RATE, mono=True)
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to load audio file. May be corrupted or unsupported format.")

        if len(audio) == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty.")

        # Validate duration
        duration = len(audio) / sr
        if duration < MIN_DURATION:
            raise HTTPException(status_code=400, detail=f"Audio too short: {duration:.1f}s (minimum {MIN_DURATION}s)")
        if duration > MAX_DURATION:
            audio = audio[:int(MAX_DURATION * sr)]

        # Step 1: Run both signals
        vaani_result = run_vaani_signal(audio, sr)
        spectra_result = run_spectra_signal(audio, sr)

        # Step 2: Combine via ensemble truth table
        ensemble_result = combine_signals(vaani_result, spectra_result)

        # Step 3: Retrieve reference evidence
        wav2vec = get_wav2vec_model()
        feat_ext = get_feature_extractor()
        reference_result = {"examples": [], "note": "", "available": False}
        if wav2vec is not None and feat_ext is not None:
            try:
                with torch.no_grad():
                    inputs = feat_ext(audio, sampling_rate=sr, return_tensors="pt")
                    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
                    outputs = wav2vec(**inputs)
                    query_emb = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
                # query_emb is now CPU numpy, but reference_index expects L2-normalized
                query_emb = query_emb / (np.linalg.norm(query_emb) + 1e-8)
                reference_result = retrieve_references(query_emb)
            except Exception as e:
                logger.warning(f"Reference retrieval failed: {e}")

        # Step 4: Build evidence object
        evidence = {
            "verdict": ensemble_result["verdict"],
            "vaani_signal": vaani_result,
            "spectra_signal": spectra_result,
            "agreement": ensemble_result["agreement"],
            "acoustic_features": vaani_result.get("acoustic_features", {}),
            "reference_examples": reference_result.get("examples", []),
            "reference_note": reference_result.get("note", ""),
        }

        # Step 5: Generate deterministic explanation
        # The engine has its own evidence-grounded fallback — never override with a static string
        try:
            explanation = generate_explanation(evidence)
        except Exception as e:
            logger.error(f"Explanation engine error (using minimal fallback): {e}")
            # Minimal evidence-derived fallback — never V1's static per-label sentence
            explanation = {
                "summary": f"Verdict: {ensemble_result['verdict']}. VAANI score: {vaani_result.get('model_score', 0):.3f}.",
                "evidence_cited": ["vaani_signal"],
                "technical_analysis": "The explanation engine encountered an internal error.",
                "recommendation": "Consult the raw analysis data for details.",
            }

        # Build response
        response = {
            "verdict": ensemble_result["verdict"],
            "confidence": ensemble_result["confidence"],
            "confidence_note": ensemble_result.get("confidence_note", ""),
            "entropy": vaani_result.get("entropy", 0.0),
            "ensemble": {
                "agreement": ensemble_result["agreement"],
                "vaani_signal": {
                    "score": vaani_result.get("model_score", 0.5),
                    "prediction": vaani_result.get("prediction", "?"),
                },
                "spectra_signal": {
                    "score": spectra_result.get("model_score", 0.5),
                    "prediction": spectra_result.get("prediction", "?"),
                    "available": spectra_result.get("available", False),
                },
                "available": not ensemble_result.get("degraded", True),
            },
            "signals": vaani_result.get("acoustic_features", {}),
            "reference_examples": reference_result.get("examples", []),
            "reference_note": reference_result.get("note", ""),
            "explanation": explanation,
            "status": "ok",
            "degraded": ensemble_result.get("degraded", False),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during analysis.")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass

    return JSONResponse(content=response)
