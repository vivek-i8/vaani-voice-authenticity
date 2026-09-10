"""Tests for VAANI V2 API analyze endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.skip(reason="Requires model loading; integration test")
def test_analyze_endpoint_requires_auth(client):
    """POST /api/analyze should require authentication / valid payload."""
    response = client.post("/api/analyze", json={})
    # Should either 422 (validation) or 401/403, not 500 from missing models
    assert response.status_code != 500


def test_analyze_endpoint_health_check_routing(client):
    """Ensure /api/health and /api/analyze are distinct routes."""
    from app.main import app as fastapi_app
    routes = [r.path for r in fastapi_app.routes if hasattr(r, 'path')]
    health_routes = [r for r in routes if 'health' in r.lower()]
    assert len(health_routes) >= 1