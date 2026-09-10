"""Deterministic ensemble truth table for VAANI V2.

Combines VAANI signal and Spectra-AASIST3 signal using a deterministic
truth table. No learned components -- pure rule-based logic.

Score normalization: both signals normalized to p(bona fide) direction.
Higher score = more human (bona fide).

Constants (per Source of Truth Sections 7, 8):
- AGREEMENT_THRESHOLD = 0.60
- ENTROPY_THRESHOLD = 0.55
"""
import numpy as np
from typing import Dict, Any


# Named constants (Section 18 of Source of Truth)
AGREEMENT_THRESHOLD = 0.60
ENTROPY_THRESHOLD = 0.55


def combine_signals(
    vaani_result: Dict[str, Any],
    spectra_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Combine two signals using the deterministic truth table.

    Args:
        vaani_result: From run_vaani_signal() -- has model_score, prediction, entropy
        spectra_result: From run_spectra_signal() -- has model_score, prediction, available

    Returns:
        Dict with verdict, confidence, agreement status, and per-signal details
    """
    vaani_score = vaani_result.get("model_score", 0.5)
    vaani_pred = vaani_result.get("prediction", "Inconclusive")
    vaani_entropy = vaani_result.get("entropy", 0.0)

    spectra_available = spectra_result.get("available", False)
    spectra_score = spectra_result.get("model_score", 0.5)
    spectra_pred = spectra_result.get("prediction", "Unavailable")

    # Degraded mode: Spectra unavailable
    if not spectra_available:
        # Use VAANI-only verdict, explicitly labeled
        if vaani_entropy > ENTROPY_THRESHOLD:
            verdict = "Inconclusive"
        elif vaani_score >= AGREEMENT_THRESHOLD:
            verdict = "Human"
        elif vaani_score <= (1.0 - AGREEMENT_THRESHOLD):
            verdict = "AI"
        else:
            verdict = "Inconclusive"

        return {
            "verdict": verdict,
            "confidence": vaani_score,
            "confidence_note": "VAANI signal only -- ensemble unavailable",
            "agreement": "single-model-only",
            "degraded": True,
            "vaani_signal": vaani_result,
            "spectra_signal": spectra_result,
        }

    # Both signals available -- apply truth table
    vaani_is_human = vaani_score >= AGREEMENT_THRESHOLD
    vaani_is_ai = vaani_score <= (1.0 - AGREEMENT_THRESHOLD)
    spectra_is_human = spectra_score >= AGREEMENT_THRESHOLD
    spectra_is_ai = spectra_score <= (1.0 - AGREEMENT_THRESHOLD)

    # Check for ambiguous bands
    vaani_ambiguous = not vaani_is_human and not vaani_is_ai
    spectra_ambiguous = not spectra_is_human and not spectra_is_ai

    # High entropy triggers Inconclusive
    if vaani_entropy > ENTROPY_THRESHOLD:
        verdict = "Inconclusive"
        agreement = "disagree" if vaani_pred != spectra_pred else "agree"
    elif vaani_ambiguous or spectra_ambiguous:
        # Ambiguous score band
        verdict = "Inconclusive"
        agreement = "disagree"
    elif vaani_is_human and spectra_is_human:
        verdict = "Human"
        agreement = "agree"
    elif vaani_is_ai and spectra_is_ai:
        verdict = "AI"
        agreement = "agree"
    else:
        # Signals disagree
        verdict = "Inconclusive"
        agreement = "disagree"

    # Confidence: average of both signals' p(bona fide)
    confidence = (vaani_score + spectra_score) / 2.0

    return {
        "verdict": verdict,
        "confidence": confidence,
        "confidence_note": "model-reported confidence, not a validated probability of correctness",
        "agreement": agreement,
        "degraded": False,
        "vaani_signal": vaani_result,
        "spectra_signal": spectra_result,
    }
