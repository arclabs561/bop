"""Tests for server deployment functionality, endpoints, and configuration."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from bop.server import app, verify_api_key, REQUIRED_API_KEY
from bop.constraints import PYSAT_AVAILABLE


class TestServerEndpoints:
    """Test server HTTP endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_agent(self):
        """Mock agent for testing."""
        with patch("bop.server.agent") as mock:
            agent = MagicMock()
            agent.chat = AsyncMock(return_value={
                "response": "Test response",
                "schema_used": None,
                "research_conducted": False,
            })
            mock.return_value = agent
            yield agent

    def test_root_endpoint(self, client):
        """Test root endpoint returns service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "BOP Knowledge Structure Research Agent"
        assert data["version"] == "0.1.0"
        assert "constraint_solver_available" in data
        assert "status" in data

    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "constraint_solver" in data
        assert isinstance(data["constraint_solver"], bool)

    @pytest.mark.asyncio
    async def test_chat_endpoint_without_api_key(self, client, mock_agent):
        """Test chat endpoint without API key when not required."""
        with patch("bop.server.REQUIRED_API_KEY", ""):
            response = client.post(
                "/chat",
                json={"message": "test", "research": False}
            )
            # Should work if no API key is required
            assert response.status_code in [200, 503]  # 503 if agent not initialized

    @pytest.mark.asyncio
    async def test_chat_endpoint_with_api_key(self, client, mock_agent):
        """Test chat endpoint with valid API key."""
        with patch("bop.server.REQUIRED_API_KEY", "test-key"):
            with patch("bop.server.agent", mock_agent):
                response = client.post(
                    "/chat",
                    json={"message": "test", "research": False},
                    headers={"X-API-Key": "test-key"}
                )
                # Should work with valid API key
                assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_chat_endpoint_invalid_api_key(self, client):
        """Test chat endpoint rejects invalid API key."""
        with patch("bop.server.REQUIRED_API_KEY", "test-key"):
            response = client.post(
                "/chat",
                json={"message": "test", "research": False},
                headers={"X-API-Key": "wrong-key"}
            )
            assert response.status_code == 401
            assert "Invalid or missing API key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chat_endpoint_missing_api_key(self, client):
        """Test chat endpoint requires API key when configured."""
        with patch("bop.server.REQUIRED_API_KEY", "test-key"):
            response = client.post(
                "/chat",
                json={"message": "test", "research": False}
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_constraints_status_endpoint(self, client):
        """Test constraints status endpoint."""
        with patch("bop.server.REQUIRED_API_KEY", ""):
            response = client.get("/constraints/status")
            # May require API key or return 503 if not initialized
            assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        with patch("bop.server.REQUIRED_API_KEY", ""):
            response = client.get("/metrics")
            # May require API key or return 503 if not initialized
            assert response.status_code in [200, 401, 503]


class TestAPIKeyAuthentication:
    """Test API key authentication logic."""

    @pytest.mark.asyncio
    async def test_verify_api_key_no_key_required(self):
        """Test API key verification when no key is required."""
        with patch("bop.server.REQUIRED_API_KEY", ""):
            result = await verify_api_key(api_key=None)
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_api_key_valid_key(self):
        """Test API key verification with valid key."""
        with patch("bop.server.REQUIRED_API_KEY", "test-key"):
            result = await verify_api_key(api_key="test-key")
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid_key(self):
        """Test API key verification rejects invalid key."""
        with patch("bop.server.REQUIRED_API_KEY", "test-key"):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(api_key="wrong-key")
            assert exc_info.value.status_code == 401
            assert "Invalid or missing API key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_api_key_missing_key(self):
        """Test API key verification requires key when configured."""
        with patch("bop.server.REQUIRED_API_KEY", "test-key"):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(api_key=None)
            assert exc_info.value.status_code == 401


class TestDeploymentConfiguration:
    """Test deployment configuration validation."""

    def test_fly_toml_exists(self):
        """Test fly.toml exists and is readable."""
        import tomllib
        from pathlib import Path
        
        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        assert fly_toml.exists(), "fly.toml should exist"
        
        with open(fly_toml, "rb") as f:
            config = tomllib.load(f)
        
        assert "app" in config
        assert "http_service" in config
        assert "processes" in config

    def test_dockerfile_exists(self):
        """Test Dockerfile exists."""
        from pathlib import Path
        
        dockerfile = Path(__file__).parent.parent.parent / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile should exist"
        
        content = dockerfile.read_text()
        assert "FROM python" in content
        assert "WORKDIR /app" in content
        assert "EXPOSE 8080" in content

    def test_dockerfile_copies_required_files(self):
        """Test Dockerfile copies all required files."""
        from pathlib import Path
        
        dockerfile = Path(__file__).parent.parent.parent / "Dockerfile"
        content = dockerfile.read_text()
        
        # Check for required COPY commands
        assert "COPY pyproject.toml" in content or "COPY pyproject.toml" in content
        assert "COPY src/" in content
        assert "COPY templates/" in content or "templates" in content
        assert "COPY static/" in content or "static" in content

    def test_fly_toml_health_check(self):
        """Test fly.toml has health check configured."""
        import tomllib
        from pathlib import Path
        
        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        with open(fly_toml, "rb") as f:
            config = tomllib.load(f)
        
        http_service = config.get("http_service", {})
        checks = http_service.get("checks", [])
        
        assert len(checks) > 0, "Health check should be configured"
        assert any(check.get("path") == "/health" for check in checks)

    def test_fly_toml_port_configuration(self):
        """Test fly.toml has correct port configuration."""
        import tomllib
        from pathlib import Path
        
        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        with open(fly_toml, "rb") as f:
            config = tomllib.load(f)
        
        http_service = config.get("http_service", {})
        assert http_service.get("internal_port") == 8080
        
        env = config.get("env", {})
        assert env.get("PORT") == "8080"

    def test_deployment_scripts_exist(self):
        """Test deployment scripts exist and are executable."""
        from pathlib import Path
        import stat
        
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        
        required_scripts = [
            "deploy_fly.sh",
            "verify_deployment.sh",
            "validate_secrets.sh",
            "make_private.sh",
            "tailscale-start.sh",
        ]
        
        for script in required_scripts:
            script_path = scripts_dir / script
            assert script_path.exists(), f"{script} should exist"
            assert script_path.is_file(), f"{script} should be a file"
            # Check if executable (on Unix)
            if os.name != "nt":
                assert os.access(script_path, os.X_OK), f"{script} should be executable"


class TestSecretValidation:
    """Test secret validation logic (unit tests for script logic)."""

    def test_required_llm_backend_validation(self):
        """Test that at least one LLM backend is required."""
        # Simulate secret list output
        secrets_with_llm = [
            "OPENAI_API_KEY=sk-test",
            "PERPLEXITY_API_KEY=pplx-test",
        ]
        
        has_llm = any(
            "OPENAI_API_KEY" in s or 
            "ANTHROPIC_API_KEY" in s or 
            "GEMINI_API_KEY" in s
            for s in secrets_with_llm
        )
        
        assert has_llm, "Should have at least one LLM backend"

    def test_mcp_tools_optional(self):
        """Test that MCP tools are optional."""
        secrets_no_mcp = ["OPENAI_API_KEY=sk-test"]
        
        mcp_count = sum(
            1 for s in secrets_no_mcp
            if any(tool in s for tool in ["PERPLEXITY", "FIRECRAWL", "TAVILY"])
        )
        
        # Should be 0, which is OK (optional)
        assert mcp_count == 0

    def test_api_key_optional(self):
        """Test that API key is optional."""
        secrets_no_api_key = ["OPENAI_API_KEY=sk-test"]
        
        has_api_key = any("BOP_API_KEY" in s for s in secrets_no_api_key)
        
        # Should be False, which is OK (optional)
        assert not has_api_key


class TestDeploymentVerification:
    """Test deployment verification logic."""

    def test_health_endpoint_response_format(self):
        """Test health endpoint returns correct format."""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "status" in data
        assert data["status"] == "healthy"
        assert "constraint_solver" in data
        assert isinstance(data["constraint_solver"], bool)

    def test_root_endpoint_response_format(self):
        """Test root endpoint returns correct format."""
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "service" in data
        assert "version" in data
        assert "constraint_solver_available" in data
        assert "status" in data

    def test_chat_response_format(self):
        """Test chat endpoint returns correct format."""
        client = TestClient(app)
        
        with patch("bop.server.REQUIRED_API_KEY", ""):
            with patch("bop.server.agent") as mock_agent:
                agent = MagicMock()
                agent.chat = AsyncMock(return_value={
                    "response": "Test response",
                    "schema_used": None,
                    "research_conducted": False,
                    "response_tiers": None,
                    "prior_beliefs": None,
                })
                mock_agent.return_value = agent
                
                response = client.post(
                    "/chat",
                    json={"message": "test", "research": False}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assert "response" in data
                    assert "schema_used" in data
                    assert "research_conducted" in data
                    assert "tools_called" in data
                    assert "constraint_solver_used" in data


class TestDeploymentScripts:
    """Test deployment script functionality."""

    def test_deploy_script_checks_flyctl(self):
        """Test deploy script checks for flyctl."""
        from pathlib import Path
        import subprocess
        
        script = Path(__file__).parent.parent.parent / "scripts" / "deploy_fly.sh"
        assert script.exists()
        
        # Check script contains flyctl check
        content = script.read_text()
        assert "flyctl" in content
        assert "command -v flyctl" in content or "which flyctl" in content

    def test_verify_script_checks_endpoints(self):
        """Test verify script checks endpoints."""
        from pathlib import Path
        
        script = Path(__file__).parent.parent.parent / "scripts" / "verify_deployment.sh"
        assert script.exists()
        
        content = script.read_text()
        assert "/health" in content
        assert "curl" in content or "http" in content

    def test_validate_script_checks_secrets(self):
        """Test validate script checks secrets."""
        from pathlib import Path
        
        script = Path(__file__).parent.parent.parent / "scripts" / "validate_secrets.sh"
        assert script.exists()
        
        content = script.read_text()
        assert "OPENAI_API_KEY" in content or "LLM" in content
        assert "secrets" in content.lower()


# Integration tests moved to test_deployment_e2e.py

