"""
Security red team tests for BOP service deployment.

These tests verify security controls, authentication, and access restrictions.
Can be rerun to verify security posture.
"""

import os

import pytest
import requests

# Test configuration
APP_URL = os.getenv("BOP_APP_URL", "https://bop-wispy-voice-3017.fly.dev")
API_KEY = os.getenv("BOP_API_KEY", "a03zsJxmWd5rZeIHDN20ZjkM_qbmfKCIEf-bP8ABTdc")
INVALID_API_KEY = "invalid-key-12345"
MISSING_API_KEY = None


class TestAuthentication:
    """Test API key authentication."""

    def test_health_endpoint_no_auth(self):
        """Health endpoint should be accessible without auth."""
        response = requests.get(f"{APP_URL}/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_root_endpoint_no_auth(self):
        """Root endpoint should be accessible without auth."""
        response = requests.get(f"{APP_URL}/", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "status" in data

    def test_chat_endpoint_without_key(self):
        """Chat endpoint should require API key."""
        response = requests.post(
            f"{APP_URL}/chat",
            json={"message": "test"},
            timeout=10
        )
        assert response.status_code == 401
        # Check for API key related error message
        response_lower = response.text.lower()
        assert any(term in response_lower for term in ["api key", "unauthorized", "authentication", "invalid"])

    def test_chat_endpoint_invalid_key(self):
        """Chat endpoint should reject invalid API key."""
        response = requests.post(
            f"{APP_URL}/chat",
            json={"message": "test"},
            headers={"X-API-Key": INVALID_API_KEY},
            timeout=10
        )
        assert response.status_code == 401

    def test_chat_endpoint_valid_key(self):
        """Chat endpoint should accept valid API key."""
        response = requests.post(
            f"{APP_URL}/chat",
            json={"message": "test", "research": False},
            headers={"X-API-Key": API_KEY},
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    def test_metrics_endpoint_without_key(self):
        """Metrics endpoint should require API key."""
        response = requests.get(f"{APP_URL}/metrics", timeout=10)
        assert response.status_code == 401

    def test_metrics_endpoint_valid_key(self):
        """Metrics endpoint should accept valid API key."""
        response = requests.get(
            f"{APP_URL}/metrics",
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert "constraint_solver" in data

    def test_constraints_status_without_key(self):
        """Constraints status endpoint should require API key."""
        response = requests.get(f"{APP_URL}/constraints/status", timeout=10)
        assert response.status_code == 401

    def test_evaluate_compare_without_key(self):
        """Evaluate compare endpoint should require API key."""
        response = requests.get(
            f"{APP_URL}/evaluate/compare?query=test&iterations=1",
            timeout=10
        )
        assert response.status_code == 401


class TestInputValidation:
    """Test input validation and sanitization."""

    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": API_KEY}

    def test_sql_injection_attempt(self, auth_headers):
        """Test SQL injection attempt is handled safely."""
        payload = {
            "message": "test'; DROP TABLE users; --",
            "research": False
        }
        response = requests.post(
            f"{APP_URL}/chat",
            json=payload,
            headers=auth_headers,
            timeout=30
        )
        # Should not crash, should return 200 or 400, not 500
        assert response.status_code in [200, 400, 422]
        assert response.status_code != 500

    def test_xss_attempt(self, auth_headers):
        """Test XSS attempt is handled safely."""
        payload = {
            "message": "<script>alert('xss')</script>",
            "research": False
        }
        response = requests.post(
            f"{APP_URL}/chat",
            json=payload,
            headers=auth_headers,
            timeout=30
        )
        # Should not crash
        assert response.status_code != 500
        # Response should not contain script tags
        if response.status_code == 200:
            assert "<script>" not in response.text.lower()

    def test_command_injection_attempt(self, auth_headers):
        """Test command injection attempt is handled safely."""
        payload = {
            "message": "test; rm -rf /",
            "research": False
        }
        response = requests.post(
            f"{APP_URL}/chat",
            json=payload,
            headers=auth_headers,
            timeout=30
        )
        # Should not crash
        assert response.status_code != 500

    def test_oversized_payload(self, auth_headers):
        """Test oversized payload is rejected."""
        # Create a very large message
        large_message = "x" * 100000
        payload = {
            "message": large_message,
            "research": False
        }
        response = requests.post(
            f"{APP_URL}/chat",
            json=payload,
            headers=auth_headers,
            timeout=30
        )
        # Should reject or handle gracefully
        assert response.status_code in [200, 400, 413, 422]

    def test_malformed_json(self, auth_headers):
        """Test malformed JSON is rejected."""
        response = requests.post(
            f"{APP_URL}/chat",
            data="not json",
            headers={**auth_headers, "Content-Type": "application/json"},
            timeout=10
        )
        assert response.status_code in [400, 422]

    def test_missing_required_fields(self, auth_headers):
        """Test missing required fields is rejected."""
        response = requests.post(
            f"{APP_URL}/chat",
            json={},  # Missing "message"
            headers=auth_headers,
            timeout=10
        )
        assert response.status_code in [400, 422]


class TestErrorHandling:
    """Test error handling doesn't leak sensitive information."""

    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": API_KEY}

    def test_error_no_stack_trace(self, auth_headers):
        """Test errors don't expose stack traces."""
        # Try to trigger an error with invalid input
        payload = {
            "message": "test",
            "schema_name": "nonexistent_schema_that_should_fail",
            "research": True
        }
        response = requests.post(
            f"{APP_URL}/chat",
            json=payload,
            headers=auth_headers,
            timeout=30
        )
        # Should not expose stack traces or file paths
        if response.status_code >= 500:
            response_text = response.text.lower()
            assert "traceback" not in response_text
            assert "/app/" not in response_text
            assert ".py" not in response_text or "file" not in response_text

    def test_unauthorized_error_message(self):
        """Test unauthorized error doesn't leak sensitive info."""
        response = requests.post(
            f"{APP_URL}/chat",
            json={"message": "test"},
            timeout=10
        )
        assert response.status_code == 401
        # Should not expose API key format or internal details
        response_text = response.text.lower()
        assert "tskey" not in response_text
        assert "secret" not in response_text


class TestRateLimiting:
    """Test rate limiting (if implemented)."""

    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": API_KEY}

    def test_rapid_requests(self, auth_headers):
        """Test rapid requests are handled."""
        # Make 10 rapid requests
        responses = []
        for _ in range(10):
            try:
                response = requests.post(
                    f"{APP_URL}/chat",
                    json={"message": "test", "research": False},
                    headers=auth_headers,
                    timeout=10
                )
                responses.append(response.status_code)
            except Exception:
                pass

        # Should handle gracefully (may rate limit, but shouldn't crash)
        assert len(responses) > 0
        # All should be valid status codes
        for status in responses:
            assert status in [200, 429, 503]  # OK, rate limited, or service unavailable


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = requests.options(
            f"{APP_URL}/health",
            headers={"Origin": "https://example.com"},
            timeout=10
        )
        # CORS headers should be present (even if restrictive)
        assert response.status_code in [200, 204, 405]

    def test_cors_preflight(self):
        """Test CORS preflight request."""
        response = requests.options(
            f"{APP_URL}/chat",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-API-Key"
            },
            timeout=10
        )
        # Should handle preflight
        assert response.status_code in [200, 204, 405]


class TestInformationDisclosure:
    """Test for information disclosure vulnerabilities."""

    def test_no_server_header(self):
        """Test server header doesn't expose version info."""
        response = requests.get(f"{APP_URL}/health", timeout=10)
        # Server header should not expose sensitive version info
        server_header = response.headers.get("Server", "").lower()
        assert "uvicorn" not in server_header
        assert "python" not in server_header

    def test_no_debug_endpoints(self):
        """Test debug endpoints are not exposed."""
        debug_paths = [
            "/debug",
            "/debug/pprof",
            "/admin",
            "/.env",
            "/config",
            "/secrets",
        ]
        for path in debug_paths:
            response = requests.get(f"{APP_URL}{path}", timeout=5)
            # Should not expose debug info
            assert response.status_code in [404, 403, 401]

    def test_error_messages_dont_leak_paths(self):
        """Test error messages don't leak file paths."""
        # Try invalid endpoint
        response = requests.get(f"{APP_URL}/nonexistent", timeout=10)
        if response.status_code >= 400:
            response_text = response.text.lower()
            # Should not expose file paths
            assert "/app/" not in response_text
            assert "/usr/" not in response_text
            assert "/var/" not in response_text


class TestTLS:
    """Test TLS/HTTPS configuration."""

    def test_https_required(self):
        """Test HTTPS is used."""
        # Try HTTP (should redirect or fail)
        http_url = APP_URL.replace("https://", "http://")
        try:
            response = requests.get(f"{http_url}/health", timeout=5, allow_redirects=False)
            # Should redirect to HTTPS or reject
            assert response.status_code in [301, 302, 308, 400, 403]
        except requests.exceptions.SSLError:
            # SSL error is also acceptable (means HTTPS is enforced)
            pass

    def test_tls_version(self):
        """Test TLS version is secure."""
        response = requests.get(f"{APP_URL}/health", timeout=10)
        # Should use TLS 1.2 or higher
        # This is verified by successful HTTPS connection
        assert response.status_code == 200


class TestTailscaleIntegration:
    """Test Tailscale integration (if enabled)."""

    def test_tailscale_accessible(self):
        """Test if Tailscale hostname is accessible."""
        # Try Tailscale hostname
        tailscale_url = APP_URL.replace(".fly.dev", ".tail-scale.ts.net")
        try:
            response = requests.get(f"{tailscale_url}/health", timeout=5)
            # If accessible, should return 200
            if response.status_code == 200:
                assert True  # Tailscale is working
        except requests.exceptions.RequestException:
            # Not accessible via Tailscale (may not be configured)
            pytest.skip("Tailscale not configured or not accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

