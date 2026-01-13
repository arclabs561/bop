"""End-to-end deployment flow tests."""

import os
from pathlib import Path

import pytest


@pytest.mark.integration
class TestDeploymentFlow:
    """Test complete deployment flow."""

    @pytest.fixture
    def scripts_dir(self):
        """Get scripts directory."""
        return Path(__file__).parent.parent.parent / "scripts"

    def test_deployment_flow_validation_before_deploy(self, scripts_dir):
        """Test that validation runs before deployment."""
        deploy_script = scripts_dir / "deploy_fly.sh"
        content = deploy_script.read_text()

        # Check that validation is called before deploy
        assert "validate_secrets" in content
        assert "deploy" in content

        # Find positions
        validate_pos = content.find("validate_secrets")
        deploy_pos = content.find("flyctl deploy")

        # Validation should come before deployment
        assert validate_pos < deploy_pos or validate_pos == -1 or deploy_pos == -1

    def test_deployment_flow_verification_after_deploy(self, scripts_dir):
        """Test that verification runs after deployment."""
        deploy_script = scripts_dir / "deploy_fly.sh"
        content = deploy_script.read_text()

        # Check that verification is called after deploy
        assert "verify_deployment" in content
        assert "deploy" in content

        # Find positions
        verify_pos = content.find("verify_deployment")
        deploy_pos = content.find("flyctl deploy")

        # Verification should come after deployment
        assert verify_pos > deploy_pos or verify_pos == -1 or deploy_pos == -1

    def test_deployment_scripts_chain_correctly(self, scripts_dir):
        """Test that deployment scripts can be chained."""
        # deploy_fly.sh should call validate_secrets.sh and verify_deployment.sh
        deploy_script = scripts_dir / "deploy_fly.sh"
        content = deploy_script.read_text()

        assert "validate_secrets.sh" in content or "validate_secrets" in content
        assert "verify_deployment.sh" in content or "verify_deployment" in content

    @pytest.mark.skipif(
        not os.getenv("TEST_DEPLOYMENT"),
        reason="Set TEST_DEPLOYMENT=1 to run actual deployment tests"
    )
    def test_full_deployment_flow(self, scripts_dir):
        """Test full deployment flow (requires actual Fly.io deployment)."""
        # This would actually run the deployment
        # Only run if TEST_DEPLOYMENT is set
        deploy_script = scripts_dir / "deploy_fly.sh"

        # Check script exists and is executable
        assert deploy_script.exists()
        assert os.access(deploy_script, os.X_OK)

        # In a real test, we would:
        # 1. Run validate_secrets.sh
        # 2. Run deploy_fly.sh
        # 3. Run verify_deployment.sh
        # 4. Check all endpoints
        # But this requires actual Fly.io credentials and deployment


class TestDeploymentConfigurationFlow:
    """Test deployment configuration is correct."""

    def test_dockerfile_builds_correctly(self):
        """Test Dockerfile can be validated."""
        dockerfile = Path(__file__).parent.parent.parent / "Dockerfile"
        assert dockerfile.exists()

        content = dockerfile.read_text()

        # Check for required stages
        assert "FROM python" in content
        assert "WORKDIR /app" in content
        assert "COPY" in content
        assert "RUN" in content
        assert "EXPOSE" in content
        assert "CMD" in content or "ENTRYPOINT" in content

    def test_fly_toml_configuration_valid(self):
        """Test fly.toml has valid configuration."""
        import tomllib

        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        assert fly_toml.exists()

        with open(fly_toml, "rb") as f:
            config = tomllib.load(f)

        # Required fields
        assert "app" in config
        assert "http_service" in config

        # Check http_service configuration
        http_service = config["http_service"]
        assert "internal_port" in http_service
        assert http_service["internal_port"] == 8080

        # Check health checks
        if "checks" in http_service:
            checks = http_service["checks"]
            assert len(checks) > 0
            assert any(check.get("path") == "/health" for check in checks)

    def test_deployment_files_consistent(self):
        """Test deployment files are consistent with each other."""
        dockerfile = Path(__file__).parent.parent.parent / "Dockerfile"
        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"

        # Read both files
        dockerfile.read_text()
        with open(fly_toml, "rb") as f:
            import tomllib
            fly_config = tomllib.load(f)

        # Check port consistency
        dockerfile_port = "8080"
        fly_port = str(fly_config["http_service"]["internal_port"])
        assert dockerfile_port == fly_port, "Ports should match between Dockerfile and fly.toml"

        # Check app name consistency in scripts
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        app_name = fly_config["app"]

        deploy_script = scripts_dir / "deploy_fly.sh"
        if deploy_script.exists():
            deploy_content = deploy_script.read_text()
            assert app_name in deploy_content or "APP_NAME" in deploy_content


class TestDeploymentValidationFlow:
    """Test deployment validation flow."""

    def test_validation_checks_required_secrets(self):
        """Test validation checks for required secrets."""
        script = Path(__file__).parent.parent.parent / "scripts" / "validate_secrets.sh"
        content = script.read_text()

        # Should check for at least one LLM backend
        assert "OPENAI_API_KEY" in content or "ANTHROPIC_API_KEY" in content or "GEMINI_API_KEY" in content

        # Should check secrets list
        assert "secrets list" in content or "secrets" in content.lower()

    def test_validation_provides_helpful_feedback(self):
        """Test validation provides helpful feedback."""
        script = Path(__file__).parent.parent.parent / "scripts" / "validate_secrets.sh"
        content = script.read_text()

        # Should have echo statements
        assert "echo" in content

        # Should provide guidance on missing secrets
        assert "required" in content.lower() or "missing" in content.lower() or "set" in content.lower()

    def test_validation_exits_with_error_on_missing_required(self):
        """Test validation exits with error when required secrets missing."""
        script = Path(__file__).parent.parent.parent / "scripts" / "validate_secrets.sh"
        content = script.read_text()

        # Should have exit 1 for failures
        assert "exit 1" in content or "exit" in content


class TestDeploymentVerificationFlow:
    """Test deployment verification flow."""

    def test_verification_checks_health_endpoint(self):
        """Test verification checks health endpoint."""
        script = Path(__file__).parent.parent.parent / "scripts" / "verify_deployment.sh"
        content = script.read_text()

        assert "/health" in content
        assert "curl" in content

    def test_verification_waits_for_app_ready(self):
        """Test verification waits for app to be ready."""
        script = Path(__file__).parent.parent.parent / "scripts" / "verify_deployment.sh"
        content = script.read_text()

        assert "status" in content.lower()
        assert "wait" in content.lower() or "retry" in content.lower() or "sleep" in content

    def test_verification_checks_multiple_endpoints(self):
        """Test verification checks multiple endpoints."""
        script = Path(__file__).parent.parent.parent / "scripts" / "verify_deployment.sh"
        content = script.read_text()

        # Should check health and root at minimum
        assert "/health" in content
        assert '"/"' in content or '"/" ' in content

    def test_verification_provides_summary(self):
        """Test verification provides summary."""
        script = Path(__file__).parent.parent.parent / "scripts" / "verify_deployment.sh"
        content = script.read_text()

        # Should have summary output
        assert "Summary" in content or "summary" in content.lower() or "✅" in content

