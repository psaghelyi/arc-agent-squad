"""
Unit tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_check():
    """Test the main health check endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "GRC Agent Squad"
    assert data["status"] == "running"
    assert data["message"] == "GRC Agent Squad is running"
    assert "timestamp" in data


def test_readiness_check():
    """Test the readiness check endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ready"
    assert data["message"] == "GRC Agent Squad is ready to serve requests"
    assert "timestamp" in data


def test_liveness_check():
    """Test the liveness check endpoint."""
    response = client.get("/health/live")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "alive"
    assert data["message"] == "GRC Agent Squad is alive"
    assert "timestamp" in data


def test_root_endpoint():
    """Test the root endpoint returns HTML."""
    response = client.get("/")
    assert response.status_code == 200
    
    # Root endpoint returns HTML, not JSON
    assert "text/html" in response.headers.get("content-type", "")
    assert "GRC Agent Squad" in response.text 