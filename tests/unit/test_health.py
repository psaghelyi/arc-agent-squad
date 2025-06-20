"""
Unit tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


def test_health_check(client):
    """Test the basic health check endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["message"] == "Voice Agent Swarm is running"
    assert data["version"] == "0.1.0"


def test_readiness_check(client):
    """Test the readiness check endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ready"
    assert data["message"] == "Voice Agent Swarm is ready to serve requests"


def test_liveness_check(client):
    """Test the liveness check endpoint."""
    response = client.get("/health/live")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "alive"
    assert data["message"] == "Voice Agent Swarm is alive"


def test_root_endpoint(client):
    """Test the root endpoint returns HTML."""
    response = client.get("/")
    assert response.status_code == 200
    
    # Root endpoint returns HTML, not JSON
    assert "text/html" in response.headers.get("content-type", "")
    assert "Agent Swarm Management" in response.text 