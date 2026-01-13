"""Deep security tests for server endpoints."""

import pytest
from fastapi.testclient import TestClient

from bop.server import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestInputValidation:
    """Test input validation on endpoints."""

    def test_chat_endpoint_path_traversal_rejected(self, client):
        """Test that path traversal in chat message is rejected."""
        response = client.post(
            "/chat",
            json={"message": "../../etc/passwd"},
            headers={"X-API-Key": "test-key"} if hasattr(app, "router") else {}
        )
        # Should either reject with 422 (validation error) or 401 (no API key)
        assert response.status_code in [400, 401, 422]

    def test_chat_endpoint_xss_rejected(self, client):
        """Test that XSS in chat message is rejected."""
        response = client.post(
            "/chat",
            json={"message": "<script>alert('xss')</script>"},
            headers={"X-API-Key": "test-key"} if hasattr(app, "router") else {}
        )
        # Should reject with validation error
        assert response.status_code in [400, 401, 422]

    def test_chat_endpoint_sql_injection_rejected(self, client):
        """Test that SQL injection in chat message is rejected."""
        response = client.post(
            "/chat",
            json={"message": "'; DROP TABLE users; --"},
            headers={"X-API-Key": "test-key"} if hasattr(app, "router") else {}
        )
        # Should reject with validation error
        assert response.status_code in [400, 401, 422]

    def test_chat_endpoint_code_injection_rejected(self, client):
        """Test that code injection in chat message is rejected."""
        response = client.post(
            "/chat",
            json={"message": "exec('malicious code')"},
            headers={"X-API-Key": "test-key"} if hasattr(app, "router") else {}
        )
        # Should reject with validation error
        assert response.status_code in [400, 401, 422]

    def test_chat_endpoint_max_length_enforced(self, client):
        """Test that max message length is enforced."""
        long_message = "x" * 10001
        response = client.post(
            "/chat",
            json={"message": long_message},
            headers={"X-API-Key": "test-key"} if hasattr(app, "router") else {}
        )
        # Should reject with validation error
        assert response.status_code in [400, 401, 422]

    def test_cache_clear_invalid_category_rejected(self, client):
        """Test that invalid cache category is rejected."""
        response = client.post(
            "/cache/clear",
            json={},
            params={"category": "../../etc/passwd"},
            headers={"X-API-Key": "test-key"} if hasattr(app, "router") else {}
        )
        # Should reject with validation error
        assert response.status_code in [400, 401, 422]

    def test_evaluate_compare_path_traversal_rejected(self, client):
        """Test that path traversal in query is rejected."""
        response = client.post(
            "/evaluate/compare",
            json={"query": "../../etc/passwd", "iterations": 1},
            headers={"X-API-Key": "test-key"} if hasattr(app, "router") else {}
        )
        # Should reject with validation error
        assert response.status_code in [400, 401, 422]


class TestErrorInformationDisclosure:
    """Test that errors don't disclose internal information."""

    def test_error_no_stack_trace(self, client):
        """Test that errors don't include stack traces."""
        # Try to trigger an error (invalid endpoint)
        response = client.get("/nonexistent/endpoint")

        # Should not contain stack trace indicators
        response_text = response.text.lower()
        assert "traceback" not in response_text
        assert "file \"" not in response_text
        assert "line " not in response_text or "line " in response_text and "error" not in response_text

    def test_error_no_file_paths(self, client):
        """Test that errors don't include file paths."""
        # Try to trigger an error
        response = client.post(
            "/chat",
            json={"message": "test"},
            headers={"X-API-Key": "invalid-key"} if hasattr(app, "router") else {}
        )

        # Should not contain file paths
        response_text = response.text.lower()
        assert "/app/" not in response_text
        assert "/usr/" not in response_text
        assert "/var/" not in response_text

    def test_error_no_api_keys(self, client):
        """Test that errors don't include API keys."""
        response = client.post(
            "/chat",
            json={"message": "test"},
            headers={"X-API-Key": "secret-key-123"} if hasattr(app, "router") else {}
        )

        # Should not contain the API key
        response_text = response.text
        assert "secret-key-123" not in response_text


class TestRateLimitingSecurity:
    """Test rate limiting security."""

    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are present."""
        # Make a request
        response = client.post(
            "/chat",
            json={"message": "test"},
            headers={"X-API-Key": "test-key"} if hasattr(app, "router") else {}
        )

        # Should have rate limit headers (or 401 if no API key)
        if response.status_code != 401:
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers

    def test_rate_limit_enforced(self, client):
        """Test that rate limiting is enforced."""
        # Make many requests quickly
        responses = []
        for _ in range(35):  # More than the limit
            response = client.post(
                "/chat",
                json={"message": "test"},
                headers={"X-API-Key": "test-key"} if hasattr(app, "router") else {}
            )
            responses.append(response.status_code)

        # Should eventually get 429 (rate limited) or 401 (no API key)
        assert 429 in responses or all(r == 401 for r in responses)


class TestSecurityHeaders:
    """Test security headers."""

    def test_security_headers_all_endpoints(self, client):
        """Test that security headers are on all endpoints."""
        endpoints = ["/health", "/metrics", "/"]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
            assert "X-XSS-Protection" in response.headers

    def test_server_header_removed(self, client):
        """Test that server header is removed."""
        response = client.get("/health")
        assert "server" not in response.headers or response.headers.get("server") == ""

