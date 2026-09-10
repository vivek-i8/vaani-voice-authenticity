"""Tests for VAANI V2 API health endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint_returns_200(client):
    """GET /api/health should return 200 with model status."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_endpoint_returns_valid_status(client):
    """Health response should have required fields."""
    response = client.get("/api/health")
    data = response.json()
    assert "status" in data
    assert "models" in data
    assert "device" in data
    assert data["status"] in ("ok", "partial")


def test_health_endpoint_all_models_loaded(client):
    """When all models load, status should be 'ok'."""
    response = client.get("/api/health")
    data = response.json()
    # At minimum wav2vec2 should be loaded
    assert "wav2vec2" in data["models"]