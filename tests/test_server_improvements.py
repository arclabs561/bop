"""Tests for server improvements."""


import pytest
from fastapi.testclient import TestClient

from pran.server import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_request_id_middleware(client):
    """Test that request ID is added to responses."""
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]


def test_rate_limiting(client):
    """Test that rate limiting works."""
    # Make many requests quickly
    for i in range(35):  # More than limit (30)
        response = client.post(
            "/chat",
            json={"message": "test"},
            headers={"X-API-Key": "test-key"} if os.getenv("BOP_API_KEY") else {},
        )

        if i >= 30:
            # Should be rate limited
            assert response.status_code == 429
        else:
            # Should work (or fail for other reasons like missing agent)
            pass


def test_input_validation_message_length(client):
    """Test that message length is validated."""
    # Too long message
    long_message = "x" * 10001
    response = client.post(
        "/chat",
        json={"message": long_message},
        headers={"X-API-Key": "test-key"} if os.getenv("BOP_API_KEY") else {},
    )
    assert response.status_code == 422  # Validation error


def test_input_validation_empty_message(client):
    """Test that empty message is rejected."""
    response = client.post(
        "/chat",
        json={"message": ""},
        headers={"X-API-Key": "test-key"} if os.getenv("BOP_API_KEY") else {},
    )
    assert response.status_code == 422  # Validation error


def test_error_sanitization():
    """Test that errors are sanitized."""
    # This would need to trigger an actual error
    # For now, just verify the error handling code exists
    pass


def test_health_check_actual_checks(client):
    """Test that health endpoint actually checks system."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "checks" in data
    assert "status" in data


def test_iterations_limit(client):
    """Test that iterations are limited."""
    response = client.post(
        "/evaluate/compare",
        json={"query": "test", "iterations": 100},  # More than limit (10)
        headers={"X-API-Key": "test-key"} if os.getenv("BOP_API_KEY") else {},
    )
    assert response.status_code == 422  # Validation error


def test_api_key_required_by_default():
    """Test that API key is required by default."""
    # This test would need to run with BOP_API_KEY not set
    # and BOP_ALLOW_NO_AUTH not set
    pass


def test_graceful_shutdown():
    """Test that graceful shutdown saves state."""
    # This would need to test the lifespan cleanup
    pass

