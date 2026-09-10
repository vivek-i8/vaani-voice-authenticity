"""Unit tests for the deterministic explanation engine."""
import pytest
from app.explainability.engine import generate_explanation


def test_human_agreement():
    evidence = {
        "verdict": "Human",
        "agreement": "agree",
        "vaani_signal": {"model_score": 0.8, "prediction": "Human", "acoustic_features": {"pitch_variance": 0.1}},
        "spectra_signal": {"model_score": 0.75, "prediction": "Human", "available": True},
        "reference_examples": [{"label": "bonafide", "similarity": 0.85}],
        "reference_note": "Compared against 100 reference clips",
    }
    result = generate_explanation(evidence)
    assert "summary" in result
    assert "evidence_cited" in result
    assert len(result["evidence_cited"]) > 0
    assert "technical_analysis" in result
    assert "recommendation" in result


def test_determinism():
    evidence = {
        "verdict": "AI",
        "agreement": "agree",
        "vaani_signal": {"model_score": 0.2, "prediction": "AI", "acoustic_features": {}},
        "spectra_signal": {"model_score": 0.25, "prediction": "AI", "available": True},
        "reference_examples": [],
        "reference_note": "No strong comparable examples found",
    }
    r1 = generate_explanation(evidence)
    r2 = generate_explanation(evidence)
    assert r1 == r2


def test_fallback():
    result = generate_explanation({})
    assert "summary" in result
    assert "evidence_cited" in result


def test_no_proof_language():
    evidence = {
        "verdict": "Human",
        "agreement": "agree",
        "vaani_signal": {"model_score": 0.8, "prediction": "Human", "acoustic_features": {}},
        "spectra_signal": {"model_score": 0.75, "prediction": "Human", "available": True},
        "reference_examples": [{"label": "bonafide", "similarity": 0.9}],
        "reference_note": "",
    }
    result = generate_explanation(evidence)
    full_text = str(result)
    # Must not use proof language
    assert "proof" not in full_text.lower()
    assert "confirmed" not in full_text.lower()
    assert "definitive" not in full_text.lower()
