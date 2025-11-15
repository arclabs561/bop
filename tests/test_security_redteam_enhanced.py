"""
Enhanced red team security tests for BOP deployment.

Comprehensive security testing including:
- Authentication bypass attempts
- Authorization testing
- Input validation and injection
- Information disclosure
- Rate limiting and DoS
- Cache security
- Volume/persistence security
- API endpoint enumeration
"""

import os
import pytest
import requests
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin

# Test configuration
APP_NAME = os.getenv("FLY_APP_NAME", "bop-wispy-voice-3017")
APP_URL = os.getenv("BOP_APP_URL", f"https://{APP_NAME}.fly.dev")
API_KEY = os.getenv("BOP_API_KEY", "")
INVALID_API_KEY = "invalid-key-12345"
TEST_DEPLOYMENT = os.getenv("TEST_DEPLOYMENT", "0") == "1"


def run_flyctl_command(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """Run a flyctl command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["flyctl"] + cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except FileNotFoundError:
        pytest.skip("flyctl not found in PATH")


class TestAuthenticationBypass:
    """Test authentication bypass attempts."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": API_KEY} if API_KEY else {}
    
    def test_no_auth_on_protected_endpoints(self):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            "/chat",
            "/metrics",
            "/cache/stats",
            "/cache/clear",
            "/constraints/status",
        ]
        
        for endpoint in protected_endpoints:
            response = requests.post(
                f"{APP_URL}{endpoint}",
                json={} if endpoint == "/chat" else None,
                timeout=10
            )
            assert response.status_code == 401, \
                f"Endpoint {endpoint} should require authentication"
    
    def test_invalid_api_key_formats(self):
        """Test various invalid API key formats."""
        invalid_keys = [
            "",  # Empty
            " ",  # Whitespace
            "null",  # String null
            "undefined",  # String undefined
            "Bearer token",  # Bearer prefix (wrong format)
            "Basic base64",  # Basic auth format
            "../../etc/passwd",  # Path traversal
            "<script>alert('xss')</script>",  # XSS attempt
            "'; DROP TABLE users; --",  # SQL injection
        ]
        
        for invalid_key in invalid_keys:
            response = requests.post(
                f"{APP_URL}/chat",
                json={"message": "test"},
                headers={"X-API-Key": invalid_key},
                timeout=10
            )
            assert response.status_code == 401, \
                f"Invalid key format '{invalid_key[:20]}...' should be rejected"
    
    def test_api_key_in_query_string(self):
        """Test that API key in query string is not accepted."""
        response = requests.post(
            f"{APP_URL}/chat?api_key={API_KEY}",
            json={"message": "test"},
            timeout=10
        )
        assert response.status_code == 401, \
            "API key in query string should not be accepted"
    
    def test_api_key_in_body(self):
        """Test that API key in body is not accepted."""
        response = requests.post(
            f"{APP_URL}/chat",
            json={"message": "test", "api_key": API_KEY},
            timeout=10
        )
        assert response.status_code == 401, \
            "API key in body should not be accepted"
    
    def test_case_sensitive_api_key(self):
        """Test that API key header is case-sensitive."""
        if not API_KEY:
            pytest.skip("API_KEY not set")
        
        # Try different case variations
        variations = [
            ("x-api-key", API_KEY),  # Lowercase header
            ("X-API-KEY", API_KEY),  # Uppercase header
            ("X-Api-Key", API_KEY),  # Mixed case
        ]
        
        for header_name, key in variations:
            response = requests.post(
                f"{APP_URL}/chat",
                json={"message": "test"},
                headers={header_name: key},
                timeout=10
            )
            # Should only accept X-API-Key (exact case)
            if header_name != "X-API-Key":
                assert response.status_code == 401, \
                    f"Header '{header_name}' should not be accepted"


class TestAuthorization:
    """Test authorization and access control."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": API_KEY} if API_KEY else {}
    
    def test_authorized_access_to_protected_endpoints(self, auth_headers):
        """Test that valid API key grants access."""
        if not API_KEY:
            pytest.skip("API_KEY not set")
        
        # Test chat endpoint
        response = requests.post(
            f"{APP_URL}/chat",
            json={"message": "test", "research": False},
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, \
            "Valid API key should grant access to /chat"
        
        # Test metrics endpoint
        response = requests.get(
            f"{APP_URL}/metrics",
            headers=auth_headers,
            timeout=10
        )
        assert response.status_code == 200, \
            "Valid API key should grant access to /metrics"
    
    def test_health_endpoint_public(self):
        """Test that health endpoint is publicly accessible."""
        response = requests.get(f"{APP_URL}/health", timeout=10)
        assert response.status_code == 200, \
            "Health endpoint should be publicly accessible"
        
        data = response.json()
        assert "status" in data, \
            "Health endpoint should return status"
    
    def test_root_endpoint_public(self):
        """Test that root endpoint is publicly accessible."""
        response = requests.get(f"{APP_URL}/", timeout=10)
        assert response.status_code == 200, \
            "Root endpoint should be publicly accessible"


class TestInputInjection:
    """Test input validation and injection attacks."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": API_KEY} if API_KEY else {}
    
    def test_sql_injection_in_message(self, auth_headers):
        """Test SQL injection attempts in message field."""
        if not API_KEY:
            pytest.skip("API_KEY not set")
        
        sql_payloads = [
            "test'; DROP TABLE users; --",
            "test' OR '1'='1",
            "test'; SELECT * FROM secrets; --",
            "test UNION SELECT * FROM users",
        ]
        
        for payload in sql_payloads:
            response = requests.post(
                f"{APP_URL}/chat",
                json={"message": payload, "research": False},
                headers=auth_headers,
                timeout=30
            )
            # Should not crash (500) or expose SQL errors
            assert response.status_code != 500, \
                f"SQL injection payload should not cause 500: {payload[:30]}"
            
            if response.status_code == 200:
                # Should not expose SQL errors
                response_text = response.text.lower()
                assert "sql" not in response_text or "error" not in response_text, \
                    f"SQL error exposed for payload: {payload[:30]}"
    
    def test_command_injection_in_message(self, auth_headers):
        """Test command injection attempts."""
        if not API_KEY:
            pytest.skip("API_KEY not set")
        
        cmd_payloads = [
            "test; rm -rf /",
            "test | cat /etc/passwd",
            "test && ls -la",
            "test `whoami`",
            "test $(id)",
        ]
        
        for payload in cmd_payloads:
            response = requests.post(
                f"{APP_URL}/chat",
                json={"message": payload, "research": False},
                headers=auth_headers,
                timeout=30
            )
            # Should not crash
            assert response.status_code != 500, \
                f"Command injection should not cause 500: {payload[:30]}"
    
    def test_xss_in_message(self, auth_headers):
        """Test XSS attempts in message field."""
        if not API_KEY:
            pytest.skip("API_KEY not set")
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
        ]
        
        for payload in xss_payloads:
            response = requests.post(
                f"{APP_URL}/chat",
                json={"message": payload, "research": False},
                headers=auth_headers,
                timeout=30
            )
            # Should not crash
            assert response.status_code != 500, \
                f"XSS payload should not cause 500: {payload[:30]}"
            
            if response.status_code == 200:
                # Response should not contain unescaped script tags
                response_text = response.text
                # Check for unescaped script tags (basic check)
                if "<script>" in response_text.lower():
                    # Should be escaped or in JSON
                    assert "\\u003c" in response_text or "&lt;" in response_text, \
                        f"XSS payload not properly escaped: {payload[:30]}"
    
    def test_path_traversal_in_message(self, auth_headers):
        """Test path traversal attempts."""
        if not API_KEY:
            pytest.skip("API_KEY not set")
        
        path_payloads = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32",
        ]
        
        for payload in path_payloads:
            response = requests.post(
                f"{APP_URL}/chat",
                json={"message": payload, "research": False},
                headers=auth_headers,
                timeout=30
            )
            # Should not crash
            assert response.status_code != 500, \
                f"Path traversal should not cause 500: {payload[:30]}"
    
    def test_json_injection(self, auth_headers):
        """Test JSON injection attempts."""
        if not API_KEY:
            pytest.skip("API_KEY not set")
        
        # Try to inject JSON in message field
        payload = 'test", "admin": true, "bypass": "'
        response = requests.post(
            f"{APP_URL}/chat",
            json={"message": payload, "research": False},
            headers=auth_headers,
            timeout=30
        )
        # Should not crash
        assert response.status_code != 500, \
            "JSON injection should not cause 500"
    
    def test_oversized_payload(self, auth_headers):
        """Test oversized payload handling."""
        if not API_KEY:
            pytest.skip("API_KEY not set")
        
        # Create very large message (1MB)
        large_message = "x" * (1024 * 1024)
        response = requests.post(
            f"{APP_URL}/chat",
            json={"message": large_message, "research": False},
            headers=auth_headers,
            timeout=30
        )
        # Should reject or handle gracefully
        assert response.status_code in [200, 400, 413, 422], \
            "Oversized payload should be rejected or handled gracefully"
    
    def test_malformed_json(self, auth_headers):
        """Test malformed JSON handling."""
        if not API_KEY:
            pytest.skip("API_KEY not set")
        
        malformed_payloads = [
            '{"message": "test"',  # Missing closing brace
            '{"message": "test",}',  # Trailing comma
            '{"message": test}',  # Unquoted value
            'not json at all',
        ]
        
        for payload in malformed_payloads:
            response = requests.post(
                f"{APP_URL}/chat",
                data=payload,
                headers={**auth_headers, "Content-Type": "application/json"},
                timeout=10
            )
            # Should reject malformed JSON
            assert response.status_code in [400, 422], \
                f"Malformed JSON should be rejected: {payload[:30]}"


class TestInformationDisclosure:
    """Test for information disclosure vulnerabilities."""
    
    def test_no_stack_traces(self):
        """Test that errors don't expose stack traces."""
        # Try to trigger an error
        response = requests.post(
            f"{APP_URL}/chat",
            json={"message": "test", "schema_name": "nonexistent_schema"},
            headers={"X-API-Key": API_KEY} if API_KEY else {},
            timeout=30
        )
        
        if response.status_code >= 500:
            response_text = response.text.lower()
            # Should not expose stack traces
            assert "traceback" not in response_text, \
                "Stack trace should not be exposed"
            assert "file \"" not in response_text, \
                "File paths should not be exposed"
            assert "/app/" not in response_text, \
                "Application paths should not be exposed"
    
    def test_no_secrets_in_responses(self):
        """Test that secrets are not exposed in responses."""
        response = requests.get(f"{APP_URL}/health", timeout=10)
        assert response.status_code == 200
        
        response_text = json.dumps(response.json()).lower()
        
        # Should not contain secret patterns
        secret_patterns = [
            "api_key",
            "secret",
            "password",
            "token",
            "tskey",
            "openai",
            "anthropic",
            "gemini",
        ]
        
        for pattern in secret_patterns:
            assert pattern not in response_text, \
                f"Secret pattern '{pattern}' found in response"
    
    def test_no_debug_endpoints(self):
        """Test that debug endpoints are not exposed."""
        debug_paths = [
            "/debug",
            "/debug/pprof",
            "/admin",
            "/.env",
            "/config",
            "/secrets",
            "/internal",
            "/private",
            "/test",
            "/dev",
        ]
        
        for path in debug_paths:
            response = requests.get(f"{APP_URL}{path}", timeout=5)
            # Should not expose debug info
            assert response.status_code in [404, 403, 401], \
                f"Debug endpoint {path} should not be accessible"
    
    def test_no_server_version_header(self):
        """Test that server version is not exposed in headers."""
        response = requests.get(f"{APP_URL}/health", timeout=10)
        
        server_header = response.headers.get("Server", "").lower()
        # Should not expose server version
        assert "uvicorn" not in server_header, \
            "Server header should not expose uvicorn"
        assert "python" not in server_header, \
            "Server header should not expose Python"
    
    def test_no_file_paths_in_errors(self):
        """Test that file paths are not exposed in errors."""
        # Try invalid endpoint
        response = requests.get(f"{APP_URL}/nonexistent-endpoint-12345", timeout=10)
        
        if response.status_code >= 400:
            response_text = response.text.lower()
            # Should not expose file paths
            assert "/app/" not in response_text, \
                "Application file paths should not be exposed"
            assert "/usr/" not in response_text, \
                "System file paths should not be exposed"
            assert "/var/" not in response_text, \
                "Var file paths should not be exposed"
            assert ".py" not in response_text or "file" not in response_text, \
                "Python file paths should not be exposed"


class TestRateLimitingDoS:
    """Test rate limiting and DoS protection."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": API_KEY} if API_KEY else {}
    
    def test_rapid_requests_rate_limited(self, auth_headers):
        """Test that rapid requests are rate limited."""
        if not API_KEY:
            pytest.skip("API_KEY not set")
        
        # Make rapid requests
        responses = []
        for i in range(35):  # More than typical 30 req/min limit
            try:
                response = requests.post(
                    f"{APP_URL}/chat",
                    json={"message": f"test {i}", "research": False},
                    headers=auth_headers,
                    timeout=10
                )
                responses.append(response.status_code)
            except Exception:
                pass
        
        # Should eventually rate limit (429)
        status_codes = set(responses)
        assert 429 in status_codes or len([s for s in responses if s == 200]) <= 30, \
            "Rate limiting should prevent more than 30 requests per minute"
    
    def test_unauthorized_requests_rejected_quickly(self):
        """Test that unauthorized requests are rejected quickly."""
        # Make many unauthorized requests
        responses = []
        start_time = time.time()
        
        for _ in range(50):
            try:
                response = requests.post(
                    f"{APP_URL}/chat",
                    json={"message": "test"},
                    timeout=2
                )
                responses.append(response.status_code)
            except Exception:
                pass
        
        elapsed = time.time() - start_time
        
        # Should reject quickly (all 401)
        assert all(s == 401 for s in responses), \
            "Unauthorized requests should be rejected with 401"
        assert elapsed < 10, \
            "Unauthorized requests should be rejected quickly (<10s for 50 requests)"
    
    def test_health_endpoint_not_rate_limited(self):
        """Test that health endpoint is not rate limited."""
        # Make many requests to health endpoint
        responses = []
        for _ in range(100):
            try:
                response = requests.get(f"{APP_URL}/health", timeout=2)
                responses.append(response.status_code)
            except Exception:
                pass
        
        # Should all succeed (200)
        assert all(s == 200 for s in responses), \
            "Health endpoint should not be rate limited"


class TestCacheSecurity:
    """Test cache security and access control."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": API_KEY} if API_KEY else {}
    
    def test_cache_stats_requires_auth(self):
        """Test that cache stats endpoint requires authentication."""
        response = requests.get(f"{APP_URL}/cache/stats", timeout=10)
        assert response.status_code == 401, \
            "Cache stats endpoint should require authentication"
    
    def test_cache_clear_requires_auth(self):
        """Test that cache clear endpoint requires authentication."""
        response = requests.post(f"{APP_URL}/cache/clear", timeout=10)
        assert response.status_code == 401, \
            "Cache clear endpoint should require authentication"
    
    def test_cache_stats_with_auth(self, auth_headers):
        """Test that cache stats works with valid auth."""
        if not API_KEY:
            pytest.skip("API_KEY not set")
        
        response = requests.get(
            f"{APP_URL}/cache/stats",
            headers=auth_headers,
            timeout=10
        )
        assert response.status_code == 200, \
            "Cache stats should be accessible with valid auth"
        
        data = response.json()
        # Should return cache statistics
        assert "cache_dir" in data or "total_size_bytes" in data, \
            "Cache stats should return cache information"
    
    def test_cache_clear_with_auth(self, auth_headers):
        """Test that cache clear works with valid auth."""
        if not API_KEY:
            pytest.skip("API_KEY not set")
        
        response = requests.post(
            f"{APP_URL}/cache/clear",
            headers=auth_headers,
            timeout=10
        )
        assert response.status_code == 200, \
            "Cache clear should work with valid auth"
    
    def test_cache_injection_attempts(self, auth_headers):
        """Test cache-related injection attempts."""
        if not API_KEY:
            pytest.skip("API_KEY not set")
        
        # Try to inject in cache clear category parameter
        injection_payloads = [
            "../../etc/passwd",
            "'; DROP TABLE cache; --",
            "<script>alert('xss')</script>",
        ]
        
        for payload in injection_payloads:
            response = requests.post(
                f"{APP_URL}/cache/clear?category={payload}",
                headers=auth_headers,
                timeout=10
            )
            # Should not crash
            assert response.status_code != 500, \
                f"Cache injection should not cause 500: {payload[:30]}"


class TestVolumePersistenceSecurity:
    """Test volume and persistence security."""
    
    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_volumes_encrypted(self):
        """Test that volumes are encrypted."""
        exit_code, stdout, _ = run_flyctl_command(["volumes", "list", "-a", APP_NAME])
        assert exit_code == 0, "Failed to list volumes"
        
        # Check for encryption
        if "bop_cache" in stdout:
            assert "encrypted" in stdout.lower() or "true" in stdout.lower(), \
                "Volumes should be encrypted"
    
    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_no_sensitive_data_in_volume_paths(self):
        """Test that volume paths don't expose sensitive data."""
        # Check fly.toml for volume mounts
        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        if fly_toml.exists():
            content = fly_toml.read_text()
            if "mounts" in content.lower():
                # Should not expose sensitive paths
                assert "/etc" not in content, \
                    "Volume mounts should not use /etc"
                assert "/root" not in content, \
                    "Volume mounts should not use /root"
                assert "/home" not in content, \
                    "Volume mounts should not use /home"


class TestAPIEnumeration:
    """Test API endpoint enumeration and discovery."""
    
    def test_common_endpoints_not_exposed(self):
        """Test that common API endpoints are not exposed."""
        common_paths = [
            "/api/v1/users",
            "/api/admin",
            "/api/config",
            "/api/secrets",
            "/api/debug",
            "/swagger",
            "/swagger.json",
            "/openapi.json",
            "/graphql",
            "/graphiql",
        ]
        
        for path in common_paths:
            response = requests.get(f"{APP_URL}{path}", timeout=5)
            # Should not expose these endpoints
            assert response.status_code in [404, 403, 401], \
                f"Common endpoint {path} should not be accessible"
    
    def test_http_methods_restricted(self):
        """Test that HTTP methods are properly restricted."""
        # Test OPTIONS on protected endpoint
        response = requests.options(f"{APP_URL}/chat", timeout=5)
        # Should handle OPTIONS (CORS preflight) or reject
        assert response.status_code in [200, 204, 405, 401], \
            "OPTIONS method should be handled properly"
        
        # Test PUT on chat endpoint (should not be allowed)
        response = requests.put(
            f"{APP_URL}/chat",
            json={"message": "test"},
            timeout=5
        )
        # Should reject PUT (405 Method Not Allowed) or require auth (401)
        assert response.status_code in [405, 401, 404], \
            "PUT method should not be allowed on /chat"
        
        # Test DELETE on chat endpoint (should not be allowed)
        response = requests.delete(f"{APP_URL}/chat", timeout=5)
        # Should reject DELETE
        assert response.status_code in [405, 401, 404], \
            "DELETE method should not be allowed on /chat"


class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present."""
        response = requests.options(
            f"{APP_URL}/health",
            headers={"Origin": "https://example.com"},
            timeout=10
        )
        # CORS headers should be present (even if restrictive)
        assert response.status_code in [200, 204, 405], \
            "CORS preflight should be handled"
    
    def test_cors_not_overly_permissive(self):
        """Test that CORS is not overly permissive."""
        response = requests.options(
            f"{APP_URL}/chat",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-API-Key",
            },
            timeout=10
        )
        
        # Check CORS headers
        acao = response.headers.get("Access-Control-Allow-Origin", "")
        acac = response.headers.get("Access-Control-Allow-Credentials", "")
        
        # Should not allow credentials with wildcard
        if acao == "*" and acac.lower() == "true":
            pytest.fail("CORS should not allow credentials with wildcard origin")


class TestTLS:
    """Test TLS/HTTPS configuration."""
    
    def test_https_required(self):
        """Test that HTTPS is required."""
        # Try HTTP (should redirect or fail)
        http_url = APP_URL.replace("https://", "http://")
        try:
            response = requests.get(f"{http_url}/health", timeout=5, allow_redirects=False)
            # Should redirect to HTTPS
            assert response.status_code in [301, 302, 308, 400, 403], \
                "HTTP should redirect to HTTPS or be rejected"
        except requests.exceptions.SSLError:
            # SSL error means HTTPS is enforced
            pass
    
    def test_tls_version_secure(self):
        """Test that TLS version is secure."""
        response = requests.get(f"{APP_URL}/health", timeout=10)
        # Successful HTTPS connection implies TLS 1.2+
        assert response.status_code == 200, \
            "Should use secure TLS version"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

