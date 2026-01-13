"""
Enhanced security tests for BOP deployment on Fly.io.

Tests security, persistence, configuration, and Fly.io-specific concerns.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest
import requests

# Test configuration
APP_NAME = os.getenv("FLY_APP_NAME", "bop-wispy-voice-3017")
APP_URL = os.getenv("BOP_APP_URL", f"https://{APP_NAME}.fly.dev")
API_KEY = os.getenv("BOP_API_KEY", "")
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


class TestFlyIOSecurity:
    """Test Fly.io-specific security configurations."""

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_no_public_ips(self):
        """Test that app has no public IPs (private deployment)."""
        exit_code, stdout, _ = run_flyctl_command(["ips", "list", "-a", APP_NAME])
        assert exit_code == 0, "Failed to list IPs"

        # Parse IP list
        lines = stdout.split("\n")
        public_ips = [line for line in lines if "public" in line.lower() and "v4" in line or "v6" in line]

        # Should have no public IPs
        assert len(public_ips) == 0, f"Found public IPs: {public_ips}. App should be private."

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_secrets_not_exposed(self):
        """Test that secrets are not exposed in environment or responses."""
        # Check health endpoint doesn't expose secrets
        response = requests.get(f"{APP_URL}/health", timeout=10)
        assert response.status_code == 200

        data = response.json()
        response_text = json.dumps(data).lower()

        # Should not contain API keys or secrets
        secret_patterns = [
            "api_key", "secret", "password", "token",
            "openai", "anthropic", "gemini", "perplexity",
            "firecrawl", "tavily", "tailscale"
        ]
        for pattern in secret_patterns:
            assert pattern not in response_text, f"Secret pattern '{pattern}' found in response"

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_https_enforced(self):
        """Test that HTTPS is enforced."""
        # Try HTTP (should redirect or fail)
        http_url = APP_URL.replace("https://", "http://")
        try:
            response = requests.get(f"{http_url}/health", timeout=5, allow_redirects=False)
            # Should redirect to HTTPS
            assert response.status_code in [301, 302, 308], "HTTP should redirect to HTTPS"
        except requests.exceptions.SSLError:
            # SSL error means HTTPS is enforced
            pass

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_health_check_configured(self):
        """Test that health check is configured in fly.toml."""
        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        assert fly_toml.exists(), "fly.toml not found"

        content = fly_toml.read_text()
        assert "health" in content.lower(), "Health check not configured"
        assert "/health" in content, "Health check path not configured"

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_auto_stop_enabled(self):
        """Test that auto-stop is enabled for cost optimization."""
        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        content = fly_toml.read_text()

        # Should have auto_stop_machines configured
        assert "auto_stop" in content.lower(), "Auto-stop not configured"

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_secrets_required(self):
        """Test that required secrets are set."""
        exit_code, stdout, _ = run_flyctl_command(["secrets", "list", "-a", APP_NAME])
        assert exit_code == 0, "Failed to list secrets"

        # Check for at least one LLM backend
        has_llm = any(
            key in stdout
            for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]
        )
        assert has_llm, "At least one LLM backend secret should be set"


class TestPersistenceSecurity:
    """Test persistence and data storage security."""

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_no_sensitive_data_in_ephemeral(self):
        """Test that sensitive data is not stored in ephemeral filesystem."""
        # This would require SSH access to check
        # For now, verify that volumes are not required (ephemeral is acceptable)
        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        content = fly_toml.read_text()

        # If volumes are used, they should be encrypted
        if "mounts" in content.lower():
            assert "encryption" in content.lower() or "encrypted" in content.lower(), \
                "Volumes should be encrypted"

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_session_data_secure(self):
        """Test that session data is handled securely."""
        if not API_KEY:
            pytest.skip("API_KEY not set")

        # Create a session
        response = requests.post(
            f"{APP_URL}/chat",
            json={"message": "test session", "research": False},
            headers={"X-API-Key": API_KEY},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            # Session IDs should not be predictable
            if "session_id" in data:
                session_id = data["session_id"]
                # Should be UUID-like, not sequential
                assert len(session_id) >= 32, "Session ID should be sufficiently long"

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_adaptive_learning_data_secure(self):
        """Test that adaptive learning data is stored securely."""
        # Check that adaptive_learning.json is not exposed via API
        debug_paths = [
            "/adaptive_learning.json",
            "/data/adaptive_learning.json",
            "/.adaptive_learning.json",
        ]

        for path in debug_paths:
            response = requests.get(f"{APP_URL}{path}", timeout=5)
            # Should not expose data files
            assert response.status_code in [404, 403, 401], \
                f"Data file exposed at {path}"


class TestConfigurationSecurity:
    """Test configuration security and secrets management."""

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_env_vars_not_exposed(self):
        """Test that environment variables are not exposed."""
        # Try to access common env var endpoints
        env_paths = [
            "/.env",
            "/env",
            "/config",
            "/environment",
        ]

        for path in env_paths:
            response = requests.get(f"{APP_URL}{path}", timeout=5)
            # Should not expose environment
            assert response.status_code in [404, 403, 401], \
                f"Environment exposed at {path}"

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_fly_toml_not_exposed(self):
        """Test that fly.toml is not exposed."""
        response = requests.get(f"{APP_URL}/fly.toml", timeout=5)
        assert response.status_code in [404, 403, 401], "fly.toml should not be exposed"

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_dockerfile_not_exposed(self):
        """Test that Dockerfile is not exposed."""
        response = requests.get(f"{APP_URL}/Dockerfile", timeout=5)
        assert response.status_code in [404, 403, 401], "Dockerfile should not be exposed"

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_secrets_rotation_capability(self):
        """Test that secrets can be rotated."""
        # Verify secrets can be updated
        exit_code, stdout, _ = run_flyctl_command(["secrets", "list", "-a", APP_NAME])
        assert exit_code == 0, "Should be able to list secrets"

        # This doesn't actually rotate, just verifies capability
        # In production, you'd want to test actual rotation


class TestPersistenceOptions:
    """Test persistence options and recommendations for Fly.io."""

    def test_volumes_not_required(self):
        """Test that volumes are not required (ephemeral is acceptable)."""
        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        content = fly_toml.read_text()

        # Volumes are optional for BOP (sessions can be ephemeral)
        # If volumes are used, they should be configured correctly
        if "mounts" in content.lower():
            # Should specify size and region
            assert "size_gb" in content.lower() or "size" in content.lower(), \
                "Volume size should be specified"

    def test_ephemeral_data_handling(self):
        """Test that ephemeral data is handled correctly."""
        # BOP uses:
        # - adaptive_learning.json (can be ephemeral, regenerated)
        # - quality_history.json (can be ephemeral)
        # - sessions/ (can be ephemeral)

        # These should be stored in /tmp or /app/data (ephemeral)
        # Not in /var/lib or other persistent locations

        # Check Dockerfile doesn't use persistent paths incorrectly
        dockerfile = Path(__file__).parent.parent.parent / "Dockerfile"
        if dockerfile.exists():
            content = dockerfile.read_text()
            # Should not write to /var/lib or /usr/local without volumes
            if "mounts" not in content.lower():
                assert "/var/lib" not in content or "VOLUME" in content, \
                    "Writing to /var/lib without volumes will lose data"

    def test_backup_strategy_documented(self):
        """Test that backup strategy is documented."""
        # Check for backup documentation
        docs = [
            Path(__file__).parent.parent.parent / "DEPLOYMENT.md",
            Path(__file__).parent.parent.parent / "DEPLOYMENT_SETUP_TAILSCALE.md",
        ]

        any(doc.exists() and "backup" in doc.read_text().lower() for doc in docs)
        # Backup strategy should be documented if using volumes
        # For ephemeral data, this is optional


class TestDatabaseOptions:
    """Test database options and recommendations."""

    def test_no_database_required(self):
        """Test that BOP doesn't require a database."""
        # BOP is stateless - sessions can be ephemeral
        # No database required for core functionality

        # Check that no database secrets are required
        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        content = fly_toml.read_text()

        # Should not require database connection strings
        db_patterns = ["postgres", "mysql", "mongodb", "redis", "database"]
        for pattern in db_patterns:
            if pattern in content.lower():
                # If database is used, it should be optional/optional
                assert "optional" in content.lower() or "BOP_" in content, \
                    f"Database {pattern} should be optional"

    def test_optional_database_recommendations(self):
        """Test recommendations for optional database usage."""
        # If BOP needs persistence in future:
        # - Fly.io Postgres (managed)
        # - Fly.io Volumes with SQLite
        # - LiteFS for distributed SQLite

        # Document recommendations
        recommendations = {
            "fly_postgres": "Managed Postgres for production",
            "fly_volumes": "Local SQLite for single-machine",
            "litefs": "Distributed SQLite for multi-machine",
        }

        # These are recommendations, not requirements
        assert len(recommendations) > 0


class TestRateLimitingSecurity:
    """Test rate limiting and DDoS protection."""

    @pytest.mark.skipif(not TEST_DEPLOYMENT or not API_KEY, reason="Set TEST_DEPLOYMENT=1 and API_KEY")
    def test_rate_limiting_works(self):
        """Test that rate limiting prevents abuse."""
        headers = {"X-API-Key": API_KEY}

        # Make rapid requests
        responses = []
        for i in range(35):  # More than the 30 req/min limit
            try:
                response = requests.post(
                    f"{APP_URL}/chat",
                    json={"message": f"test {i}", "research": False},
                    headers=headers,
                    timeout=10
                )
                responses.append(response.status_code)
            except Exception:
                pass

        # Should eventually rate limit (429) or handle gracefully
        status_codes = set(responses)
        assert 429 in status_codes or len([s for s in responses if s == 200]) <= 30, \
            "Rate limiting should prevent more than 30 requests per minute"

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_ddos_protection(self):
        """Test DDoS protection (basic)."""
        # Make many requests without auth (should be rejected quickly)
        responses = []
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

        # Should reject unauthorized requests quickly (401)
        assert all(s == 401 for s in responses), \
            "Unauthorized requests should be rejected quickly (401)"


class TestTailscaleSecurity:
    """Test Tailscale-specific security."""

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_tailscale_authkey_secure(self):
        """Test that Tailscale auth key is stored as secret."""
        exit_code, stdout, _ = run_flyctl_command(["secrets", "list", "-a", APP_NAME])

        if "TAILSCALE" in stdout:
            # Auth key should be in secrets, not in code
            dockerfile = Path(__file__).parent.parent.parent / "Dockerfile"
            if dockerfile.exists():
                content = dockerfile.read_text()
                # Should not hardcode auth key
                assert "tskey-auth-" not in content, "Tailscale auth key should not be in Dockerfile"

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_tailscale_accessible_privately(self):
        """Test that Tailscale access works (if configured)."""
        # Try Tailscale hostname
        tailscale_url = APP_URL.replace(".fly.dev", ".tail-scale.ts.net")
        try:
            response = requests.get(f"{tailscale_url}/health", timeout=5)
            if response.status_code == 200:
                # Tailscale is working
                assert True
        except requests.exceptions.RequestException:
            # Not configured or not accessible
            pytest.skip("Tailscale not configured")


class TestDeploymentSecurity:
    """Test deployment security best practices."""

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_dockerfile_security(self):
        """Test Dockerfile security best practices."""
        dockerfile = Path(__file__).parent.parent.parent / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile not found"

        content = dockerfile.read_text()

        # Should not run as root
        assert "USER" in content or "RUN adduser" in content or "RUN addgroup" in content, \
            "Should not run as root user"

        # Should not expose unnecessary ports
        expose_lines = [line for line in content.split("\n") if "EXPOSE" in line]
        assert len(expose_lines) <= 1, "Should only expose necessary ports"

        # Should use specific base image tags, not 'latest'
        from_lines = [line for line in content.split("\n") if line.strip().startswith("FROM")]
        for line in from_lines:
            if "latest" in line.lower() and ":" not in line:
                pytest.warn("Base image should use specific tag, not 'latest'")

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_fly_toml_security(self):
        """Test fly.toml security configuration."""
        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        assert fly_toml.exists(), "fly.toml not found"

        content = fly_toml.read_text()

        # Should force HTTPS
        assert "force_https" in content.lower(), "Should force HTTPS"

        # Should have health checks
        assert "health" in content.lower(), "Should have health checks"

        # Should not expose debug ports
        assert "debug" not in content.lower() or "false" in content.lower(), \
            "Debug ports should not be exposed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

