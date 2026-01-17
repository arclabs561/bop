"""Tests for request size limit middleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from pran.request_limits import RequestSizeLimitMiddleware


@pytest.fixture
def test_app():
    """Create a test FastAPI app."""
    app = FastAPI()

    @app.post("/test")
    async def test_endpoint(request: dict):
        return {"status": "ok", "received": len(str(request))}

    return app


@pytest.fixture
def client_with_limits(test_app):
    """Client with request size limits."""
    test_app.add_middleware(RequestSizeLimitMiddleware, max_body_size=1024, max_header_size=512, max_query_string_size=256)
    return TestClient(test_app)


class TestRequestSizeLimits:
    """Test request size limiting."""

    def test_normal_request_allowed(self, client_with_limits):
        """Test that normal-sized requests are allowed."""
        response = client_with_limits.post("/test", json={"data": "test"})
        assert response.status_code == 200

    def test_large_body_rejected(self, client_with_limits):
        """Test that large request bodies are rejected."""
        large_data = "x" * 2048  # Larger than 1024 byte limit
        response = client_with_limits.post("/test", json={"data": large_data})
        assert response.status_code == 413
        assert "too large" in response.json()["error"]["message"].lower()

    def test_large_query_string_rejected(self, client_with_limits):
        """Test that large query strings are rejected."""
        large_query = "x" * 512  # Larger than 256 byte limit
        response = client_with_limits.get(f"/test?param={large_query}")
        assert response.status_code == 413

    def test_get_request_no_body_limit(self, client_with_limits):
        """Test that GET requests don't have body size limits."""
        response = client_with_limits.get("/test")
        # Should not fail due to body size (GET has no body)
        # 405 = Method Not Allowed (endpoint exists but doesn't support GET)
        assert response.status_code in [200, 404, 405]  # 404 if endpoint doesn't exist, 405 if method not allowed

    def test_size_limit_response_format(self, client_with_limits):
        """Test that size limit responses have correct format."""
        large_data = "x" * 2048
        response = client_with_limits.post("/test", json={"data": large_data})
        assert response.status_code == 413

        data = response.json()
        assert "error" in data
        assert "message" in data["error"]
        assert "max_size" in data["error"]

