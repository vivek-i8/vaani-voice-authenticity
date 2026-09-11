"""V1 API route tests.

Fully offline: the Wav2Vec2 pipeline is monkeypatched with a deterministic
fake so tests cover routing/contract/decision plumbing, not the backbone.
"""
import io
import numpy as np
import soundfile as sf
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    from app.main import app

    def fake_run_inference(audio, sampling_rate=16000):
        entropy = 0.1
        return {
            "label": "Human",
            "confidence": 0.9,
            "entropy": entropy,
            "human_probability": 0.9,
            "signals": {
                "pitch_variance": 12.5,
                "spectral_drift": 340.2,
                "zcr_variance": 0.0021,
            },
        }

    # Patch where the names are actually used (they are imported into these
    # modules' namespaces, not looked up on app.ml.inference at call time).
    monkeypatch.setattr("app.api.analyze.run_inference", fake_run_inference)
    monkeypatch.setattr("app.services.single_clip.run_inference", fake_run_inference)

    # Health warmup should not load models during tests; report ready.
    # (main.py imported initialize_model into its own namespace, and routes.py
    # reads state via get_model_state -> patch both at their usage sites.)
    monkeypatch.setattr("app.main.initialize_model", lambda: None)
    monkeypatch.setattr("app.ml.model_loader._model_state", {"status": "ready", "error": None})

    with TestClient(app) as c:
        yield c


def _wav_bytes(seconds=4.0, sr=16000):
    rng = np.random.RandomState(7)
    audio = (0.2 * rng.randn(int(sr * seconds))).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV")
    return buf.getvalue()


def test_health_reports_ready_pipeline(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["device"] in ("cpu", "cuda")


def test_active_analyze_contract_and_mock_explanation(client):
    res = client.post(
        "/api/analyze/",
        files={"file": ("test.wav", _wav_bytes(), "audio/wav")},
    )
    assert res.status_code == 200
    body = res.json()

    # V1 response contract
    assert body["label"] in ("Human", "AI", "Inconclusive")
    assert 0.0 <= body["confidence"] <= 1.0
    assert 0.0 <= body["entropy"]
    assert set(body["signals"].keys()) == {"pitch_variance", "spectral_drift", "zcr_variance"}
    assert body["human_probability"] == pytest.approx(0.9)

    # Structured explanation from MockLLM (USE_LLM=false default)
    assert body["explanation"]["summary"]
    assert body["explanation"]["technical_analysis"]
    assert body["explanation"]["recommendation"]
    assert body["explanation"]["model"]
    assert body["explanation_source"] == "mock"


def test_active_analyze_rejects_non_audio(client):
    res = client.post(
        "/api/analyze/",
        files={"file": ("x.txt", b"not audio", "text/plain")},
    )
    assert res.status_code == 400


def test_legacy_analyze_contract(client):
    res = client.post(
        "/api/v1/analyze",
        data={"language": "en"},
        files={"audio": ("test.wav", _wav_bytes(), "audio/wav")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["classification"] in ("human", "ai_generated", "inconclusive")
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["explanation"]["primary_language"] == "en"
    assert body["explanation"]["text"]
    assert body["explanation"]["advisory"]


def test_legacy_batch_analyze_contract(client):
    res = client.post(
        "/api/v1/analyze/batch",
        data={"language": "en"},
        files=[
            ("audio_files", ("a.wav", _wav_bytes(), "audio/wav")),
            ("audio_files", ("b.wav", _wav_bytes(), "audio/wav")),
        ],
    )
    assert res.status_code == 200
    body = res.json()
    assert body["classification"] in ("human", "ai_generated", "inconclusive")
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["explanation"]["text"]
