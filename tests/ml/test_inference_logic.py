"""V1 tests: artifact compatibility, decision logic, fusion head shape.

All offline: loads only the local .pth/.pkl artifacts, never the network.
"""
import numpy as np
import pytest
import torch


def test_fusion_head_architecture_matches_v1_metadata():
    from app.ml.inference import FusionHead

    model = FusionHead(input_dim=1027, hidden_dims=[256, 64], output_dim=2, dropout=0.3)
    logits = model(torch.zeros(1, 1027))
    assert logits.shape == (1, 2)


def test_artifacts_load_and_are_compatible():
    import joblib
    from app.ml.inference import FusionHead

    scaler = joblib.load("models/vaani_model/scaler.pkl")
    model = FusionHead(input_dim=1027, hidden_dims=[256, 64], output_dim=2, dropout=0.3)
    model.load_state_dict(torch.load("models/vaani_model/fusion_head.pth", map_location="cpu"))

    features = np.zeros((1, 1027), dtype=np.float32)
    scaled = scaler.transform(features)
    assert scaled.shape == (1, 1027)

    probs = model.predict_proba(torch.tensor(scaled, dtype=torch.float32))
    assert probs.shape == (1, 2)
    assert abs(probs.sum().item() - 1.0) < 1e-5


def test_entropy_decision_threshold_055():
    from app.ml.inference import _compute_entropy, _make_decision

    # Confident prediction -> low entropy -> decided label
    confident = np.array([0.95, 0.05])
    entropy = _compute_entropy(confident)
    assert entropy < 0.55
    label, confidence = _make_decision(confident, entropy)
    assert label == "Human"
    assert confidence == pytest.approx(0.95)

    # Uniform prediction -> high entropy -> Inconclusive
    uniform = np.array([0.5, 0.5])
    assert _compute_entropy(uniform) > 0.55
    label, _ = _make_decision(uniform, _compute_entropy(uniform))
    assert label == "Inconclusive"

    # Confident AI prediction
    ai = np.array([0.05, 0.95])
    label, _ = _make_decision(ai, _compute_entropy(ai))
    assert label == "AI"
