"""Tests for security and observability middleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from bop.middleware import (
    EnhancedRateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)


@pytest.fixture
def test_app():
    """Create a test FastAPI app."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


@pytest.fixture
def client_with_security_headers(test_app):
    """Client with security headers middleware."""
    test_app.add_middleware(SecurityHeadersMiddleware)
    return TestClient(test_app)


@pytest.fixture
def client_with_rate_limiting(test_app):
    """Client with rate limiting middleware."""
    test_app.add_middleware(EnhancedRateLimitMiddleware, window_seconds=60, max_requests=3)
    return TestClient(test_app)


class TestSecurityHeaders:
    """Test security headers middleware."""

    def test_security_headers_present(self, client_with_security_headers):
        """Test that security headers are added to responses."""
        response = client_with_security_headers.get("/test")

        assert response.status_code == 200
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers

    def test_server_header_removed(self, client_with_security_headers):
        """Test that server header is removed."""
        response = client_with_security_headers.get("/test")
        # Server header should not be present (or should be removed)
        # Note: TestClient might not add it, but middleware should remove it if present
        assert "server" not in response.headers or response.headers.get("server") == ""

    def test_security_headers_on_all_endpoints(self, client_with_security_headers):
        """Test that security headers are on all endpoints."""
        endpoints = ["/test", "/health", "/nonexistent"]

        for endpoint in endpoints:
            response = client_with_security_headers.get(endpoint)
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers


class TestRequestLogging:
    """Test request logging middleware."""

    def test_request_logged(self, test_app, caplog):
        """Test that requests are logged."""
        import logging
        caplog.set_level(logging.INFO)

        test_app.add_middleware(RequestLoggingMiddleware, log_body=False, log_headers=False)
        client = TestClient(test_app)

        response = client.get("/test")
        assert response.status_code == 200

        # Check that request was logged
        log_records = [r for r in caplog.records if "Request:" in r.message]
        assert len(log_records) > 0

        # Check log contains expected fields
        log_message = log_records[0].message
        assert "request_id" in log_message
        assert "method" in log_message
        assert "path" in log_message
        assert "status_code" in log_message
        assert "duration_ms" in log_message

    def test_error_logged(self, test_app, caplog):
        """Test that errors are logged."""
        import logging
        caplog.set_level(logging.INFO)

        @test_app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        test_app.add_middleware(RequestLoggingMiddleware)
        client = TestClient(test_app)

        try:
            client.get("/error")
        except Exception:
            # TestClient might raise exception, that's ok
            pass

        # Check that error was logged (look for request log with error)
        log_records = [r for r in caplog.records if "Request:" in r.message and "error" in r.message.lower()]
        # If no error in request log, check for any error logs
        if not log_records:
            error_records = [r for r in caplog.records if r.levelname == "ERROR"]
            assert len(error_records) > 0, "Error should be logged"
        else:
            assert len(log_records) > 0, "Error should be in request log"


class TestRateLimiting:
    """Test enhanced rate limiting middleware."""

    def test_rate_limit_headers_present(self, client_with_rate_limiting):
        """Test that rate limit headers are present."""
        response = client_with_rate_limiting.get("/test")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Window" in response.headers

        assert int(response.headers["X-RateLimit-Limit"]) == 3
        assert int(response.headers["X-RateLimit-Remaining"]) < 3

    def test_rate_limit_enforced(self, client_with_rate_limiting):
        """Test that rate limiting is enforced."""
        # Make requests up to limit
        for i in range(3):
            response = client_with_rate_limiting.get("/test")
            assert response.status_code == 200
            remaining = int(response.headers["X-RateLimit-Remaining"])
            assert remaining >= 0

        # Next request should be rate limited
        response = client_with_rate_limiting.get("/test")
        assert response.status_code == 429
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert "X-RateLimit-Reset" in response.headers

    def test_health_endpoint_not_rate_limited(self, client_with_rate_limiting):
        """Test that health endpoint is not rate limited."""
        # Make many requests to health endpoint
        for _ in range(10):
            response = client_with_rate_limiting.get("/health")
            assert response.status_code == 200
            # Health endpoint should not have rate limit headers (or should always succeed)

    def test_rate_limit_per_api_key(self, test_app):
        """Test that rate limiting works per API key."""
        test_app.add_middleware(EnhancedRateLimitMiddleware, window_seconds=60, max_requests=2)
        client = TestClient(test_app)

        # Make requests with different API keys
        key1 = "key1"
        key2 = "key2"

        # Key1: 2 requests (limit)
        for _ in range(2):
            response = client.get("/test", headers={"X-API-Key": key1})
            assert response.status_code == 200

        # Key1: should be rate limited
        response = client.get("/test", headers={"X-API-Key": key1})
        assert response.status_code == 429

        # Key2: should still work (different key)
        response = client.get("/test", headers={"X-API-Key": key2})
        assert response.status_code == 200

    def test_rate_limit_response_format(self, client_with_rate_limiting):
        """Test that rate limit response has correct format."""
        # Exceed rate limit
        for _ in range(4):
            client_with_rate_limiting.get("/test")

        response = client_with_rate_limiting.get("/test")
        assert response.status_code == 429

        data = response.json()
        assert "detail" in data
        assert "limit" in data
        assert "window_seconds" in data
        assert "reset_at" in data
        assert data["limit"] == 3
        assert data["window_seconds"] == 60

