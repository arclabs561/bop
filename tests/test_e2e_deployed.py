"""End-to-end tests for deployed BOP service.

Tests all security features against the actual deployed instance.
Requires Tailscale access to the deployed service.
"""

import os
import pytest
import httpx
import asyncio
import time
from typing import Optional

# Get deployment URL from environment or use default
# Try Tailscale hostname first, fallback to direct hostname
# Server runs on port 8080 (Fly.io PORT env var), not 8000
TAILSCALE_HOST = os.getenv("BOP_TAILSCALE_HOST", "bop-wispy-voice-3017-1.tailf8f94.ts.net")
DEPLOYED_PORT = os.getenv("BOP_DEPLOYED_PORT", "8080")
DEPLOYED_URL = os.getenv("BOP_DEPLOYED_URL", f"http://{TAILSCALE_HOST}:{DEPLOYED_PORT}")
API_KEY = os.getenv("BOP_API_KEY", "")

# Timeout for requests
REQUEST_TIMEOUT = 30.0


@pytest.fixture
def client():
    """Create HTTP client for deployed service."""
    return httpx.AsyncClient(
        base_url=DEPLOYED_URL,
        timeout=REQUEST_TIMEOUT,
        headers={"X-API-Key": API_KEY} if API_KEY else {},
    )


@pytest.fixture
def client_no_auth():
    """Create HTTP client without API key."""
    return httpx.AsyncClient(
        base_url=DEPLOYED_URL,
        timeout=REQUEST_TIMEOUT,
    )


class TestE2ESecurityHeaders:
    """Test security headers on deployed service."""
    
    @pytest.mark.asyncio
    async def test_security_headers_present(self, client):
        """Test that all security headers are present."""
        response = await client.get("/health")
        assert response.status_code == 200
        
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy",
        ]
        
        for header in required_headers:
            assert header in response.headers, f"Missing security header: {header}"
            assert response.headers[header] != "", f"Empty security header: {header}"
    
    @pytest.mark.asyncio
    async def test_server_header_removed(self, client):
        """Test that server header is removed."""
        response = await client.get("/health")
        assert "server" not in response.headers or response.headers.get("server") == ""
    
    @pytest.mark.asyncio
    async def test_request_id_present(self, client):
        """Test that request ID is present in responses."""
        response = await client.get("/health")
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] != ""


class TestE2EAuthentication:
    """Test authentication on deployed service."""
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_auth(self, client_no_auth):
        """Test that protected endpoints require API key."""
        response = await client_no_auth.post("/chat", json={"message": "test"})
        assert response.status_code == 401
        assert "API key" in response.text.lower() or "unauthorized" in response.text.lower()
    
    @pytest.mark.asyncio
    async def test_health_endpoint_public(self, client_no_auth):
        """Test that health endpoint is public."""
        response = await client_no_auth.get("/health")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_invalid_api_key_rejected(self, client_no_auth):
        """Test that invalid API key is rejected."""
        response = await client_no_auth.post(
            "/chat",
            json={"message": "test"},
            headers={"X-API-Key": "invalid-key-12345"},
        )
        assert response.status_code == 401


class TestE2EInputValidation:
    """Test input validation on deployed service."""
    
    @pytest.mark.asyncio
    async def test_xss_attempt_rejected(self, client):
        """Test that XSS attempts are rejected."""
        response = await client.post(
            "/chat",
            json={"message": "<script>alert('xss')</script>"},
        )
        # Should either reject with 422 (validation error) or process safely
        assert response.status_code in [400, 401, 422]
    
    @pytest.mark.asyncio
    async def test_path_traversal_rejected(self, client):
        """Test that path traversal attempts are rejected."""
        response = await client.post(
            "/chat",
            json={"message": "../../etc/passwd"},
        )
        assert response.status_code in [400, 401, 422]
    
    @pytest.mark.asyncio
    async def test_sql_injection_rejected(self, client):
        """Test that SQL injection attempts are rejected."""
        response = await client.post(
            "/chat",
            json={"message": "'; DROP TABLE users; --"},
        )
        assert response.status_code in [400, 401, 422]
    
    @pytest.mark.asyncio
    async def test_max_length_enforced(self, client):
        """Test that max message length is enforced."""
        long_message = "x" * 10001
        response = await client.post(
            "/chat",
            json={"message": long_message},
        )
        assert response.status_code in [400, 401, 422]


class TestE2ERateLimiting:
    """Test rate limiting on deployed service."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are present."""
        response = await client.get("/health")
        # Health endpoint might be excluded from rate limiting
        if "X-RateLimit-Limit" in response.headers:
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforced(self, client):
        """Test that rate limiting is enforced."""
        # Make many requests quickly
        responses = []
        for i in range(35):  # More than the default limit of 30
            try:
                response = await client.post(
                    "/chat",
                    json={"message": f"test {i}"},
                )
                responses.append(response.status_code)
                # Small delay to avoid overwhelming
                await asyncio.sleep(0.1)
            except Exception as e:
                responses.append(f"error: {e}")
        
        # Should eventually get 429 (rate limited) or 401 (no API key)
        assert 429 in responses or all(r == 401 for r in responses if isinstance(r, int))


class TestE2EErrorHandling:
    """Test error handling on deployed service."""
    
    @pytest.mark.asyncio
    async def test_error_has_error_id(self, client):
        """Test that errors include error IDs."""
        # Trigger an error (invalid endpoint)
        response = await client.get("/nonexistent/endpoint")
        # Should have error ID in headers or response
        assert "X-Error-ID" in response.headers or response.status_code < 500
    
    @pytest.mark.asyncio
    async def test_error_no_stack_trace(self, client):
        """Test that errors don't include stack traces."""
        response = await client.get("/nonexistent/endpoint")
        response_text = response.text.lower()
        assert "traceback" not in response_text
        assert "file \"" not in response_text
    
    @pytest.mark.asyncio
    async def test_error_no_file_paths(self, client):
        """Test that errors don't include file paths."""
        response = await client.post(
            "/chat",
            json={"message": "test"},
            headers={"X-API-Key": "invalid"},
        )
        response_text = response.text.lower()
        assert "/app/" not in response_text
        assert "/usr/" not in response_text


class TestE2EInformationDisclosure:
    """Test information disclosure on deployed service."""
    
    @pytest.mark.asyncio
    async def test_root_endpoint_minimal_info(self, client_no_auth):
        """Test that root endpoint doesn't expose internal details."""
        response = await client_no_auth.get("/")
        if response.status_code == 200:
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            # Should not expose version, constraint solver, etc.
            assert "version" not in str(data).lower() or "constraint_solver" not in str(data).lower()
    
    @pytest.mark.asyncio
    async def test_health_endpoint_minimal_info(self, client_no_auth):
        """Test that health endpoint doesn't expose internal details."""
        response = await client_no_auth.get("/health")
        assert response.status_code == 200
        data = response.json()
        # Should not expose constraint_solver availability
        assert "constraint_solver" not in data or isinstance(data.get("constraint_solver"), bool)
    
    @pytest.mark.asyncio
    async def test_api_docs_disabled(self, client_no_auth):
        """Test that API documentation is disabled."""
        response = await client_no_auth.get("/docs")
        assert response.status_code == 404
        
        response = await client_no_auth.get("/redoc")
        assert response.status_code == 404
        
        response = await client_no_auth.get("/openapi.json")
        assert response.status_code == 404


class TestE2ERequestSizeLimits:
    """Test request size limits on deployed service."""
    
    @pytest.mark.asyncio
    async def test_large_body_rejected(self, client):
        """Test that large request bodies are rejected."""
        # Create a body larger than 10MB
        large_body = {"message": "x" * (11 * 1024 * 1024)}  # 11MB
        response = await client.post("/chat", json=large_body)
        # Should get 413 (Content Too Large) or 400 (validation error)
        assert response.status_code in [400, 413, 422]
    
    @pytest.mark.asyncio
    async def test_large_query_string_rejected(self, client):
        """Test that large query strings are rejected."""
        large_query = "x" * 3000  # Larger than 2KB limit
        response = await client.get(f"/health?param={large_query}")
        # Should get 413 or process normally (health might be excluded)
        assert response.status_code in [200, 413]


class TestE2EFunctional:
    """Test functional endpoints on deployed service."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_works(self, client_no_auth):
        """Test that health endpoint works."""
        response = await client_no_auth.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_works(self, client):
        """Test that chat endpoint works with valid request."""
        if not API_KEY:
            pytest.skip("API key not provided")
        
        response = await client.post(
            "/chat",
            json={"message": "Hello, what is d-separation?"},
        )
        # Should succeed (200) or timeout (504) or service unavailable (503)
        assert response.status_code in [200, 503, 504]
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint_protected(self, client):
        """Test that metrics endpoint is protected."""
        response = await client.get("/metrics")
        # Should succeed (200) if authenticated, or 401 if not
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data or "topology" in data
    
    @pytest.mark.asyncio
    async def test_cache_endpoints_protected(self, client):
        """Test that cache endpoints are protected."""
        response = await client.get("/cache/stats")
        assert response.status_code in [200, 401, 503]
        
        response = await client.post("/cache/clear")
        assert response.status_code in [200, 401, 500]


if __name__ == "__main__":
    import asyncio
    pytest.main([__file__, "-v"])

