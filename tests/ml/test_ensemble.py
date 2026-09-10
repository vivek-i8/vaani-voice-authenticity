"""Unit tests for the ensemble truth table."""
import pytest
from app.ml.ensemble import combine_signals, AGREEMENT_THRESHOLD, ENTROPY_THRESHOLD


def test_both_agree_human():
    vaani = {"model_score": 0.8, "prediction": "Human", "entropy": 0.2}
    spectra = {"model_score": 0.75, "prediction": "Human", "available": True}
    result = combine_signals(vaani, spectra)
    assert result["verdict"] == "Human"
    assert result["agreement"] == "agree"
    assert result["degraded"] == False


def test_both_agree_ai():
    vaani = {"model_score": 0.2, "prediction": "AI", "entropy": 0.3}
    spectra = {"model_score": 0.25, "prediction": "AI", "available": True}
    result = combine_signals(vaani, spectra)
    assert result["verdict"] == "AI"
    assert result["agreement"] == "agree"


def test_disagree():
    vaani = {"model_score": 0.8, "prediction": "Human", "entropy": 0.2}
    spectra = {"model_score": 0.2, "prediction": "AI", "available": True}
    result = combine_signals(vaani, spectra)
    assert result["verdict"] == "Inconclusive"
    assert result["agreement"] == "disagree"


def test_high_entropy():
    vaani = {"model_score": 0.55, "prediction": "Human", "entropy": 0.7}
    spectra = {"model_score": 0.7, "prediction": "Human", "available": True}
    result = combine_signals(vaani, spectra)
    assert result["verdict"] == "Inconclusive"


def test_degraded_mode():
    vaani = {"model_score": 0.8, "prediction": "Human", "entropy": 0.2}
    spectra = {"model_score": 0.0, "prediction": "Unavailable", "available": False}
    result = combine_signals(vaani, spectra)
    assert result["verdict"] == "Human"
    assert result["degraded"] == True
    assert result["agreement"] == "single-model-only"


def test_ambiguous_band():
    vaani = {"model_score": 0.55, "prediction": "Human", "entropy": 0.3}
    spectra = {"model_score": 0.55, "prediction": "Human", "available": True}
    result = combine_signals(vaani, spectra)
    assert result["verdict"] == "Inconclusive"
