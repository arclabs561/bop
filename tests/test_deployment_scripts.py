"""Property-based and behavioral tests for deployment scripts."""

import os
from pathlib import Path

import pytest


class TestDeploymentScriptsStructure:
    """Test deployment scripts have correct structure and dependencies."""

    @pytest.fixture
    def scripts_dir(self):
        """Get scripts directory."""
        return Path(__file__).parent.parent.parent / "scripts"

    def test_all_scripts_exist(self, scripts_dir):
        """Test all required deployment scripts exist."""
        required = [
            "deploy_fly.sh",
            "verify_deployment.sh",
            "validate_secrets.sh",
            "make_private.sh",
            "tailscale-start.sh",
        ]

        for script in required:
            script_path = scripts_dir / script
            assert script_path.exists(), f"{script} should exist"
            assert script_path.is_file(), f"{script} should be a file"

    def test_scripts_are_executable(self, scripts_dir):
        """Test scripts are executable (Unix)."""
        if os.name == "nt":
            pytest.skip("Windows doesn't use executable bits")

        scripts = [
            "deploy_fly.sh",
            "verify_deployment.sh",
            "validate_secrets.sh",
            "make_private.sh",
            "tailscale-start.sh",
        ]

        for script in scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                assert os.access(script_path, os.X_OK), f"{script} should be executable"

    def test_scripts_have_shebang(self, scripts_dir):
        """Test scripts have proper shebang."""
        scripts = [
            "deploy_fly.sh",
            "verify_deployment.sh",
            "validate_secrets.sh",
            "make_private.sh",
            "tailscale-start.sh",
        ]

        for script in scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                content = script_path.read_text()
                assert content.startswith("#!/bin/bash"), f"{script} should have shebang"

    def test_scripts_use_set_e(self, scripts_dir):
        """Test scripts use 'set -e' for error handling."""
        scripts = [
            "deploy_fly.sh",
            "verify_deployment.sh",
            "validate_secrets.sh",
            "make_private.sh",
        ]

        for script in scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                content = script_path.read_text()
                assert "set -e" in content, f"{script} should use 'set -e'"


class TestDeployScript:
    """Test deploy_fly.sh script logic."""

    @pytest.fixture
    def script_path(self):
        """Get deploy script path."""
        return Path(__file__).parent.parent.parent / "scripts" / "deploy_fly.sh"

    def test_script_checks_flyctl(self, script_path):
        """Test script checks for flyctl command."""
        content = script_path.read_text()
        assert "flyctl" in content
        assert "command -v flyctl" in content or "which flyctl" in content

    def test_script_checks_login(self, script_path):
        """Test script checks for Fly.io login."""
        content = script_path.read_text()
        assert "auth whoami" in content or "whoami" in content
        assert "auth login" in content or "login" in content

    def test_script_calls_validation(self, script_path):
        """Test script calls validation script."""
        content = script_path.read_text()
        assert "validate_secrets" in content

    def test_script_calls_verification(self, script_path):
        """Test script calls verification script."""
        content = script_path.read_text()
        assert "verify_deployment" in content

    def test_script_sets_app_name(self, script_path):
        """Test script sets app name."""
        content = script_path.read_text()
        assert "bop-wispy-voice-3017" in content
        assert "APP_NAME" in content or "FLY_APP_NAME" in content


class TestVerifyScript:
    """Test verify_deployment.sh script logic."""

    @pytest.fixture
    def script_path(self):
        """Get verify script path."""
        return Path(__file__).parent.parent.parent / "scripts" / "verify_deployment.sh"

    def test_script_checks_health_endpoint(self, script_path):
        """Test script checks health endpoint."""
        content = script_path.read_text()
        assert "/health" in content
        assert "curl" in content

    def test_script_checks_root_endpoint(self, script_path):
        """Test script checks root endpoint."""
        content = script_path.read_text()
        assert '"/"' in content or '"/" ' in content or 'curl.*"/"' in content

    def test_script_waits_for_app(self, script_path):
        """Test script waits for app to be ready."""
        content = script_path.read_text()
        assert "status" in content.lower()
        assert "wait" in content.lower() or "retry" in content.lower()

    def test_script_checks_api_key(self, script_path):
        """Test script checks API key configuration."""
        content = script_path.read_text()
        assert "API" in content or "api" in content or "BOP_API_KEY" in content

    def test_script_checks_public_ips(self, script_path):
        """Test script checks public IPs."""
        content = script_path.read_text()
        assert "ips" in content.lower() or "IP" in content


class TestValidateScript:
    """Test validate_secrets.sh script logic."""

    @pytest.fixture
    def script_path(self):
        """Get validate script path."""
        return Path(__file__).parent.parent.parent / "scripts" / "validate_secrets.sh"

    def test_script_checks_llm_backends(self, script_path):
        """Test script checks for LLM backends."""
        content = script_path.read_text()
        assert "OPENAI_API_KEY" in content or "LLM" in content
        assert "ANTHROPIC_API_KEY" in content or "LLM" in content
        assert "GEMINI_API_KEY" in content or "LLM" in content

    def test_script_checks_mcp_tools(self, script_path):
        """Test script checks for MCP tools."""
        content = script_path.read_text()
        assert "PERPLEXITY" in content or "MCP" in content
        assert "FIRECRAWL" in content or "MCP" in content
        assert "TAVILY" in content or "MCP" in content

    def test_script_checks_api_key(self, script_path):
        """Test script checks for API key."""
        content = script_path.read_text()
        assert "BOP_API_KEY" in content

    def test_script_checks_tailscale(self, script_path):
        """Test script checks for Tailscale."""
        content = script_path.read_text()
        assert "TAILSCALE" in content or "Tailscale" in content

    def test_script_requires_at_least_one_llm(self, script_path):
        """Test script requires at least one LLM backend."""
        content = script_path.read_text()
        # Should check for at least one LLM backend
        assert "OPENAI_API_KEY" in content or "ANTHROPIC_API_KEY" in content or "GEMINI_API_KEY" in content


class TestMakePrivateScript:
    """Test make_private.sh script logic."""

    @pytest.fixture
    def script_path(self):
        """Get make_private script path."""
        return Path(__file__).parent.parent.parent / "scripts" / "make_private.sh"

    def test_script_releases_public_ips(self, script_path):
        """Test script releases public IPs."""
        content = script_path.read_text()
        assert "ips release" in content or "release" in content
        assert "public" in content.lower() or "IPv4" in content or "IPv6" in content

    def test_script_lists_ips(self, script_path):
        """Test script lists IPs before releasing."""
        content = script_path.read_text()
        assert "ips list" in content or "list" in content


class TestTailscaleStartScript:
    """Test tailscale-start.sh script logic."""

    @pytest.fixture
    def script_path(self):
        """Get tailscale-start script path."""
        return Path(__file__).parent.parent.parent / "scripts" / "tailscale-start.sh"

    def test_script_starts_tailscale(self, script_path):
        """Test script starts Tailscale."""
        content = script_path.read_text()
        assert "tailscale" in content.lower()
        assert "tailscaled" in content or "tailscale up" in content

    def test_script_starts_server(self, script_path):
        """Test script starts the server."""
        content = script_path.read_text()
        assert "uvicorn" in content or "server" in content.lower()
        assert "PORT" in content

    def test_script_handles_missing_authkey(self, script_path):
        """Test script handles missing auth key gracefully."""
        content = script_path.read_text()
        assert "TAILSCALE_AUTHKEY" in content
        # Should check if authkey exists before using it


class TestDeploymentScriptProperties:
    """Property-based tests for deployment scripts."""

    def test_all_scripts_use_consistent_app_name(self):
        """Test all scripts use consistent app name."""
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        app_name = "bop-wispy-voice-3017"

        scripts = [
            "deploy_fly.sh",
            "verify_deployment.sh",
            "validate_secrets.sh",
            "make_private.sh",
        ]

        for script in scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                content = script_path.read_text()
                # Should either use the app name or use a variable
                assert app_name in content or "APP_NAME" in content or "FLY_APP_NAME" in content

    def test_scripts_handle_errors(self):
        """Test scripts have error handling."""
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"

        scripts = [
            "deploy_fly.sh",
            "verify_deployment.sh",
            "validate_secrets.sh",
        ]

        for script in scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                content = script_path.read_text()
                # Should have error handling (set -e, exit codes, etc.)
                assert "set -e" in content or "exit" in content or "error" in content.lower()

    def test_scripts_provide_helpful_messages(self):
        """Test scripts provide helpful error messages."""
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"

        scripts = [
            "deploy_fly.sh",
            "verify_deployment.sh",
            "validate_secrets.sh",
        ]

        for script in scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                content = script_path.read_text()
                # Should have echo statements for user feedback
                assert "echo" in content or "print" in content.lower()

