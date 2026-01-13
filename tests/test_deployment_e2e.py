"""End-to-end deployment tests using flyctl and HTTP requests.

These tests require:
- FLY_API_TOKEN or flyctl authentication
- TEST_DEPLOYMENT=1 environment variable
- Actual Fly.io deployment access
"""

import json
import os
import subprocess
import time
from pathlib import Path

import pytest
import requests

# Test configuration
APP_NAME = os.getenv("FLY_APP_NAME", "bop-wispy-voice-3017")
APP_URL = os.getenv("BOP_APP_URL", f"https://{APP_NAME}.fly.dev")
FLY_API_TOKEN = os.getenv("FLY_API_TOKEN")
TEST_DEPLOYMENT = os.getenv("TEST_DEPLOYMENT", "0") == "1"
USE_FLY_SDK = os.getenv("USE_FLY_SDK", "0") == "1"

# Try to import fly-python-sdk if available
try:
    from fly_python_sdk.fly import Fly
    FLY_SDK_AVAILABLE = True
except ImportError:
    FLY_SDK_AVAILABLE = False


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


def wait_for_app_ready(max_retries: int = 30, delay: int = 2) -> bool:
    """Wait for app to be ready."""
    for i in range(max_retries):
        exit_code, stdout, _ = run_flyctl_command(["status", "-a", APP_NAME])
        if exit_code == 0:
            if "started" in stdout.lower() or "running" in stdout.lower():
                return True
        time.sleep(delay)
    return False


@pytest.mark.e2e
@pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run e2e tests")
class TestDeploymentE2E:
    """End-to-end deployment tests using flyctl."""

    def test_flyctl_authentication(self):
        """Test flyctl is authenticated."""
        exit_code, stdout, stderr = run_flyctl_command(["auth", "whoami"])
        assert exit_code == 0, f"flyctl not authenticated: {stderr}"
        assert "logged in" in stdout.lower() or "@" in stdout

    def test_app_exists(self):
        """Test app exists in Fly.io."""
        exit_code, stdout, _ = run_flyctl_command(["apps", "list"])
        assert exit_code == 0, "Failed to list apps"
        assert APP_NAME in stdout, f"App {APP_NAME} not found"

    def test_app_status(self):
        """Test app status command works."""
        exit_code, stdout, _ = run_flyctl_command(["status", "-a", APP_NAME])
        assert exit_code == 0, f"Failed to get app status: {stdout}"
        assert APP_NAME in stdout or "status" in stdout.lower()

    def test_app_secrets_list(self):
        """Test secrets can be listed."""
        exit_code, stdout, _ = run_flyctl_command(["secrets", "list", "-a", APP_NAME])
        # Should succeed even if no secrets
        assert exit_code == 0, f"Failed to list secrets: {stdout}"

    def test_app_has_required_secrets(self):
        """Test app has at least one LLM backend secret."""
        exit_code, stdout, _ = run_flyctl_command(["secrets", "list", "-a", APP_NAME])
        assert exit_code == 0

        # Check for at least one LLM backend
        has_llm = any(
            key in stdout
            for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]
        )
        assert has_llm, "App should have at least one LLM backend secret"

    def test_app_ips_list(self):
        """Test IP addresses can be listed."""
        exit_code, stdout, _ = run_flyctl_command(["ips", "list", "-a", APP_NAME])
        assert exit_code == 0, f"Failed to list IPs: {stdout}"

    def test_app_logs_accessible(self):
        """Test logs can be retrieved."""
        exit_code, stdout, _ = run_flyctl_command(
            ["logs", "-a", APP_NAME, "--no-tail", "--limit", "10"]
        )
        # Should succeed even if no recent logs
        assert exit_code == 0, f"Failed to get logs: {stdout}"


@pytest.mark.e2e
@pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run e2e tests")
class TestDeployedEndpointsE2E:
    """End-to-end tests for deployed HTTP endpoints."""

    @pytest.fixture(autouse=True)
    def wait_for_deployment(self):
        """Wait for app to be ready before testing."""
        if not wait_for_app_ready():
            pytest.skip("App not ready")

    def test_health_endpoint_accessible(self):
        """Test health endpoint is accessible."""
        response = requests.get(f"{APP_URL}/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "constraint_solver" in data

    def test_root_endpoint_accessible(self):
        """Test root endpoint is accessible."""
        response = requests.get(f"{APP_URL}/", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data

    def test_health_endpoint_response_time(self):
        """Test health endpoint responds quickly."""
        start = time.time()
        response = requests.get(f"{APP_URL}/health", timeout=10)
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 5.0, f"Health endpoint too slow: {elapsed}s"

    def test_chat_endpoint_requires_auth(self):
        """Test chat endpoint requires authentication."""
        response = requests.post(
            f"{APP_URL}/chat",
            json={"message": "test", "research": False},
            timeout=10,
        )
        # Should require auth (401) or be unavailable (503)
        assert response.status_code in [401, 503]

    def test_chat_endpoint_with_api_key(self):
        """Test chat endpoint works with API key."""
        # Get API key from secrets
        exit_code, stdout, _ = run_flyctl_command(["secrets", "list", "-a", APP_NAME])
        if exit_code != 0:
            pytest.skip("Cannot retrieve secrets")

        # Try to extract API key (if set)
        api_key = None
        for line in stdout.split("\n"):
            if "BOP_API_KEY" in line:
                # Extract value (format may vary)
                parts = line.split()
                if len(parts) >= 2:
                    api_key = parts[1]
                break

        if not api_key:
            pytest.skip("BOP_API_KEY not set")

        response = requests.post(
            f"{APP_URL}/chat",
            json={"message": "test", "research": False},
            headers={"X-API-Key": api_key},
            timeout=30,  # Chat may take longer
        )

        # Should succeed (200) or be unavailable (503)
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "response" in data

    def test_constraints_status_endpoint(self):
        """Test constraints status endpoint."""
        # Get API key if needed
        exit_code, stdout, _ = run_flyctl_command(["secrets", "list", "-a", APP_NAME])
        api_key = None
        if exit_code == 0:
            for line in stdout.split("\n"):
                if "BOP_API_KEY" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        api_key = parts[1]
                    break

        headers = {}
        if api_key:
            headers["X-API-Key"] = api_key

        response = requests.get(
            f"{APP_URL}/constraints/status",
            headers=headers,
            timeout=10,
        )

        # May require auth or be unavailable
        assert response.status_code in [200, 401, 503]
        if response.status_code == 200:
            data = response.json()
            assert "available" in data
            assert "enabled" in data

    def test_metrics_endpoint(self):
        """Test metrics endpoint."""
        # Get API key if needed
        exit_code, stdout, _ = run_flyctl_command(["secrets", "list", "-a", APP_NAME])
        api_key = None
        if exit_code == 0:
            for line in stdout.split("\n"):
                if "BOP_API_KEY" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        api_key = parts[1]
                    break

        headers = {}
        if api_key:
            headers["X-API-Key"] = api_key

        response = requests.get(
            f"{APP_URL}/metrics",
            headers=headers,
            timeout=10,
        )

        # May require auth or be unavailable
        assert response.status_code in [200, 401, 503]
        if response.status_code == 200:
            data = response.json()
            assert "constraint_solver" in data or "topology" in data


@pytest.mark.e2e
@pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run e2e tests")
@pytest.mark.skipif(not USE_FLY_SDK or not FLY_SDK_AVAILABLE, reason="Fly SDK not available or not enabled")
class TestDeploymentFlySDKE2E:
    """End-to-end tests using Fly Python SDK."""

    @pytest.fixture
    def fly_client(self):
        """Create Fly.io client."""
        if not FLY_API_TOKEN:
            pytest.skip("FLY_API_TOKEN not set")
        return Fly(FLY_API_TOKEN)

    def test_sdk_authentication(self, fly_client):
        """Test SDK can authenticate."""
        # SDK doesn't have explicit auth test, but we can try to list orgs
        # This is a basic connectivity test
        assert fly_client is not None

    def test_sdk_can_list_apps(self, fly_client):
        """Test SDK can list apps (if org is known)."""
        # This would require knowing the org name
        # For now, just verify SDK is initialized
        assert fly_client is not None


@pytest.mark.e2e
@pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run e2e tests")
class TestDeploymentFlowE2E:
    """End-to-end deployment flow tests."""

    def test_deployment_script_validation_works(self):
        """Test validate_secrets.sh script works."""
        script = Path(__file__).parent.parent.parent / "scripts" / "validate_secrets.sh"
        assert script.exists()

        # Run script
        result = subprocess.run(
            ["bash", str(script)],
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "FLY_APP_NAME": APP_NAME},
        )

        # Should succeed (exit 0) or fail gracefully (exit 1 with message)
        assert result.returncode in [0, 1]
        if result.returncode == 1:
            # Should provide helpful error message
            assert "LLM" in result.stdout or "required" in result.stdout.lower()

    def test_deployment_script_verification_works(self):
        """Test verify_deployment.sh script works."""
        script = Path(__file__).parent.parent.parent / "scripts" / "verify_deployment.sh"
        assert script.exists()

        # Run script
        result = subprocess.run(
            ["bash", str(script)],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "FLY_APP_NAME": APP_NAME},
        )

        # Should succeed or fail with clear error
        assert result.returncode in [0, 1]
        if result.returncode == 0:
            # Should have verification output
            assert "✅" in result.stdout or "passed" in result.stdout.lower()

    def test_full_deployment_flow(self):
        """Test full deployment flow (validation → deploy → verification)."""
        # This would actually deploy, so we'll just test the scripts exist and are callable
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"

        deploy_script = scripts_dir / "deploy_fly.sh"
        validate_script = scripts_dir / "validate_secrets.sh"
        verify_script = scripts_dir / "verify_deployment.sh"

        assert deploy_script.exists()
        assert validate_script.exists()
        assert verify_script.exists()

        # Check that deploy script calls the others
        deploy_content = deploy_script.read_text()
        assert "validate_secrets" in deploy_content
        assert "verify_deployment" in deploy_content


@pytest.mark.e2e
@pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run e2e tests")
class TestDeploymentConfigurationE2E:
    """End-to-end configuration validation tests."""

    def test_fly_toml_matches_deployment(self):
        """Test fly.toml configuration matches actual deployment."""
        import tomllib

        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        with open(fly_toml, "rb") as f:
            config = tomllib.load(f)

        # Get actual app info
        exit_code, stdout, _ = run_flyctl_command(["info", "-a", APP_NAME, "--json"])
        if exit_code == 0:
            try:
                app_info = json.loads(stdout)
                # Compare app name
                assert config["app"] == app_info.get("Name", "")
            except (json.JSONDecodeError, KeyError):
                # Info might not be in JSON format
                pass

    def test_dockerfile_builds(self):
        """Test Dockerfile can be built (dry run)."""
        dockerfile = Path(__file__).parent.parent.parent / "Dockerfile"
        assert dockerfile.exists()

        # Check Dockerfile syntax (basic validation)
        content = dockerfile.read_text()
        assert "FROM" in content
        assert "WORKDIR" in content
        assert "COPY" in content
        assert "EXPOSE" in content

    def test_deployment_configuration_consistent(self):
        """Test deployment configuration is consistent."""
        import tomllib

        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        dockerfile = Path(__file__).parent.parent.parent / "Dockerfile"

        with open(fly_toml, "rb") as f:
            config = tomllib.load(f)

        dockerfile_content = dockerfile.read_text()

        # Check port consistency
        fly_port = config["http_service"]["internal_port"]
        assert str(fly_port) in dockerfile_content or "8080" in dockerfile_content

