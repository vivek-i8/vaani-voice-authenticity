"""VAANI V2 inference pipeline.

Runs both signals independently:
1. VAANI signal (required) — Wav2Vec2 embeddings + acoustic features → fusion head
2. Spectra-AASIST3 signal (optional) — independent anti-spoofing model

Both produce raw model outputs. Verdict logic lives exclusively in ensemble.py.
"""
import torch
import numpy as np
import logging
from typing import Dict, Any

from app.ml.acoustic_features import (
    compute_pitch_variance,
    compute_spectral_centroid_drift,
    compute_zcr_variance,
)
from app.ml.model_loader import (
    get_wav2vec_model,
    get_feature_extractor,
    get_fusion_model,
    get_scaler,
    get_spectra_model,
)
from app.core.device import DEVICE

logger = logging.getLogger(__name__)


def _extract_wav2vec2_embedding(
    audio: np.ndarray, sampling_rate: int = 16000
) -> np.ndarray:
    wav2vec_model = get_wav2vec_model()
    feature_extractor = get_feature_extractor()
    if wav2vec_model is None or feature_extractor is None:
        raise RuntimeError("Wav2Vec2 model not loaded")
    with torch.no_grad():
        input_values = feature_extractor(
            audio, sampling_rate=sampling_rate, return_tensors="pt"
        ).input_values.to(DEVICE)
        outputs = wav2vec_model(input_values)
        embeddings = outputs.last_hidden_state.mean(dim=1)
        embedding = embeddings.squeeze().cpu().numpy()
        if embedding.ndim > 1:
            embedding = embedding.mean(axis=0)
        if embedding.size != 1024:
            if embedding.size > 1024:
                embedding = embedding[:1024]
            else:
                embedding = np.pad(embedding, (0, 1024 - embedding.size))
    return embedding


def _extract_acoustic_features(
    audio: np.ndarray, sampling_rate: int = 16000
) -> np.ndarray:
    pitch_var = compute_pitch_variance(audio, sampling_rate)
    spec_centroid_drift = compute_spectral_centroid_drift(audio, sampling_rate)
    zcr_var = compute_zcr_variance(audio, sampling_rate)
    return np.array([pitch_var, spec_centroid_drift, zcr_var])


def _compute_entropy(probabilities: np.ndarray) -> float:
    eps = 1e-8
    probabilities = np.clip(probabilities, eps, 1 - eps)
    entropy = -np.sum(probabilities * np.log(probabilities))
    return float(entropy)


def run_vaani_signal(audio: np.ndarray, sampling_rate: int = 16000) -> Dict[str, Any]:
    """Run the VAANI fusion signal on preprocessed audio.

    Returns dict with model_score, prediction, entropy, and acoustic_features.
    Verdict logic (Human/AI/Inconclusive) is NOT applied here — that belongs to ensemble.py.
    """
    fusion_model = get_fusion_model()
    scaler = get_scaler()
    if fusion_model is None:
        raise RuntimeError("Fusion model not loaded")
    if scaler is None:
        raise RuntimeError("Scaler not loaded")

    wav2vec2_embedding = _extract_wav2vec2_embedding(audio, sampling_rate)
    acoustic_features = _extract_acoustic_features(audio, sampling_rate)
    feature_vector = np.concatenate([wav2vec2_embedding, acoustic_features])

    if feature_vector.shape[0] != 1027:
        raise ValueError(f"Invalid feature size: expected 1027, got {feature_vector.shape[0]}")

    feature_vector = scaler.transform(feature_vector.reshape(1, -1)).squeeze()
    features_tensor = torch.FloatTensor(feature_vector).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        probabilities = fusion_model.predict_proba(features_tensor)
        probs_np = probabilities.squeeze().cpu().numpy()

    # Raw model output — no verdict logic here
    # probs_np[0] = p(bona fide/Human), probs_np[1] = p(spoof/AI)
    model_score = float(probs_np[0])  # higher = more human
    entropy = _compute_entropy(probs_np)

    return {
        "model_score": model_score,
        "prediction": "Human" if probs_np[0] > probs_np[1] else "AI",
        "entropy": entropy,
        "acoustic_features": {
            "pitch_variance": float(acoustic_features[0]),
            "spectral_drift": float(acoustic_features[1]),
            "zcr_variance": float(acoustic_features[2]),
        },
    }


def run_spectra_signal(audio: np.ndarray, sampling_rate: int = 16000) -> Dict[str, Any]:
    """Run the Spectra-AASIST3 signal on preprocessed audio.

    Returns dict with model_score, prediction, and available flag.
    """
    spectra_model = get_spectra_model()
    if spectra_model is None or not spectra_model.is_loaded:
        return {"model_score": 0.0, "prediction": "Unavailable", "available": False}
    try:
        raw_score = spectra_model.score(audio, sampling_rate)
        p_bona_fide = 1.0 / (1.0 + np.exp(-raw_score))
        prediction = "Human" if raw_score > 0 else "AI"
        return {"model_score": p_bona_fide, "prediction": prediction, "available": True}
    except Exception as e:
        logger.error(f"Spectra-AASIST3 inference failed: {e}")
        return {"model_score": 0.0, "prediction": "Error", "available": False}
