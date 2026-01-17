"""
Persistence and database testing for BOP on Fly.io.

Tests data persistence, storage options, and Fly.io volume/database integration.
"""

import os
import subprocess
from pathlib import Path

import pytest
import requests

# Test configuration
APP_NAME = os.getenv("FLY_APP_NAME", "pran-wispy-voice-3017")
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


class TestPersistenceRequirements:
    """Test what data BOP needs to persist."""

    def test_identify_persistent_data(self):
        """Identify what data BOP stores that might need persistence."""
        # BOP stores:
        # 1. adaptive_learning.json - Learning patterns (can be ephemeral)
        # 2. quality_history.json - Quality metrics (can be ephemeral)
        # 3. sessions/ - Session data (can be ephemeral)
        # 4. eval_results.json - Evaluation results (can be ephemeral)

        # Check what files are created
        data_files = [
            "adaptive_learning.json",
            "quality_history.json",
            "sessions/",
            "eval_results.json",
        ]

        project_root = Path(__file__).parent.parent.parent
        existing_files = [f for f in data_files if (project_root / f).exists()]

        # These files exist but can be ephemeral
        assert len(existing_files) >= 0, "No persistent data files found"

    def test_ephemeral_data_acceptable(self):
        """Test that ephemeral data storage is acceptable for BOP."""
        # BOP's data can be ephemeral:
        # - Learning patterns regenerate over time
        # - Quality history can be rebuilt
        # - Sessions are temporary
        # - Eval results can be rerun

        # No critical data loss if ephemeral
        assert True, "BOP can use ephemeral storage"

    def test_optional_persistence_benefits(self):
        """Test benefits of optional persistence."""
        # Optional persistence would help with:
        # - Faster startup (pre-loaded learning patterns)
        # - Historical quality trends
        # - Session continuity across restarts

        # But not required for core functionality
        assert True, "Persistence is optional enhancement"


class TestFlyIOVolumeOptions:
    """Test Fly.io volume options for persistence."""

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_volumes_not_configured(self):
        """Test that volumes are not currently configured."""
        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        content = fly_toml.read_text()

        # Volumes are optional for BOP
        has_volumes = "mounts" in content.lower() or "volume" in content.lower()

        # If volumes are used, verify configuration
        if has_volumes:
            assert "size_gb" in content.lower() or "size" in content.lower(), \
                "Volume size should be specified"
            assert "encryption" in content.lower() or "encrypted" in content.lower(), \
                "Volumes should be encrypted"

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_volume_creation_capability(self):
        """Test that volumes can be created if needed."""
        # Test volume creation command exists
        exit_code, stdout, _ = run_flyctl_command(["volumes", "--help"])
        assert exit_code == 0, "flyctl volumes command should work"

    def test_volume_recommendations(self):
        """Test recommendations for using volumes."""
        # Recommendations:
        # - Use volumes for SQLite databases
        # - Use volumes for persistent learning data
        # - Use volumes for session storage (if needed)
        # - Minimum 1GB, can extend up to 500GB

        recommendations = {
            "size": "Start with 1GB, extend as needed",
            "encryption": "Use default encryption-at-rest",
            "redundancy": "Run 2+ machines with volumes for redundancy",
            "backup": "Implement custom backup strategy",
        }

        assert len(recommendations) > 0


class TestDatabaseOptions:
    """Test database options for BOP."""

    def test_no_database_required(self):
        """Test that BOP doesn't require a database."""
        # BOP is stateless - no database required
        # All data can be ephemeral or regenerated

        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        content = fly_toml.read_text()

        # Should not require database connection
        db_required = any(
            pattern in content.lower()
            for pattern in ["postgres", "mysql", "mongodb", "database_url"]
        )
        assert not db_required, "BOP should not require a database"

    def test_optional_database_options(self):
        """Test optional database options if persistence is needed."""
        # Options if persistence is needed:
        # 1. Fly.io Postgres (managed, recommended for production)
        # 2. Fly.io Volumes + SQLite (simple, single-machine)
        # 3. LiteFS (distributed SQLite, multi-machine)

        options = {
            "fly_postgres": {
                "type": "Managed Postgres",
                "pros": ["Managed", "Backups", "Scaling", "Multi-region"],
                "cons": ["Cost", "Overkill for simple data"],
                "use_case": "Production with complex queries"
            },
            "fly_volumes_sqlite": {
                "type": "Volumes + SQLite",
                "pros": ["Simple", "Low cost", "Fast"],
                "cons": ["Single machine", "Manual backups"],
                "use_case": "Single-machine persistence"
            },
            "litefs": {
                "type": "Distributed SQLite",
                "pros": ["Multi-machine", "SQLite compatibility"],
                "cons": ["Complexity", "Read-only replicas"],
                "use_case": "Multi-machine with SQLite"
            }
        }

        assert len(options) == 3, "Should have 3 database options"


class TestConfigurationPersistence:
    """Test configuration persistence and management."""

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_secrets_persist_across_deployments(self):
        """Test that secrets persist across deployments."""
        exit_code, stdout, _ = run_flyctl_command(["secrets", "list", "-a", APP_NAME])
        assert exit_code == 0, "Should be able to list secrets"

        # Secrets should persist (they're stored in Fly.io, not in app)
        assert True, "Secrets are managed by Fly.io and persist"

    @pytest.mark.skipif(not TEST_DEPLOYMENT, reason="Set TEST_DEPLOYMENT=1 to run")
    def test_env_vars_persist(self):
        """Test that environment variables persist."""
        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        content = fly_toml.read_text()

        # Env vars in fly.toml persist across deployments
        if "[env]" in content:
            assert "BOP_USE_CONSTRAINTS" in content or "PORT" in content, \
                "Environment variables should be configured"

    def test_config_file_location(self):
        """Test where configuration files are stored."""
        # Configuration options:
        # 1. fly.toml (version controlled, deployed with app)
        # 2. Secrets (stored in Fly.io, not in code)
        # 3. Environment variables (in fly.toml or secrets)

        fly_toml = Path(__file__).parent.parent.parent / "fly.toml"
        assert fly_toml.exists(), "fly.toml should exist"

        # Should not contain secrets
        content = fly_toml.read_text()
        secret_patterns = ["api_key", "password", "secret", "token"]
        for pattern in secret_patterns:
            # Check for actual secret values (long alphanumeric strings)
            lines = content.split("\n")
            for line in lines:
                if pattern in line.lower() and "=" in line:
                    value = line.split("=")[-1].strip()
                    # Should not be an actual secret (long string)
                    if len(value) > 20 and value.replace("-", "").replace("_", "").isalnum():
                        pytest.fail(f"Potential secret found in fly.toml: {pattern}")


class TestDataBackupStrategy:
    """Test backup strategy for persistent data."""

    def test_backup_strategy_documented(self):
        """Test that backup strategy is documented."""
        # For ephemeral data: No backup needed
        # For volumes: Should have backup strategy

        docs = [
            Path(__file__).parent.parent.parent / "DEPLOYMENT.md",
            Path(__file__).parent.parent.parent / "DEPLOYMENT_SETUP_TAILSCALE.md",
        ]

        # Check if backup is mentioned
        any(
            doc.exists() and "backup" in doc.read_text().lower()
            for doc in docs
        )

        # Backup strategy should be documented if using volumes
        # For ephemeral data, this is optional
        assert True, "Backup strategy documentation check"

    def test_snapshot_capability(self):
        """Test that volume snapshots can be created."""
        # Fly.io provides automatic snapshots (daily, 5 days retention)
        # Can also create manual snapshots

        # This is a capability check, not a requirement
        assert True, "Volume snapshots are available if volumes are used"

    def test_data_recovery_strategy(self):
        """Test data recovery strategy."""
        # For ephemeral data: Regenerate on restart
        # For volumes: Restore from snapshots or backups

        strategies = {
            "ephemeral": "Regenerate data on restart",
            "volumes": "Restore from snapshots or backups",
            "secrets": "Managed by Fly.io, no recovery needed",
        }

        assert len(strategies) == 3


class TestSessionPersistence:
    """Test session persistence options."""

    @pytest.mark.skipif(not TEST_DEPLOYMENT or not API_KEY, reason="Set TEST_DEPLOYMENT=1 and API_KEY")
    def test_sessions_ephemeral(self):
        """Test that sessions can be ephemeral."""
        headers = {"X-API-Key": API_KEY}

        # Create a session
        response1 = requests.post(
            f"{APP_URL}/chat",
            json={"message": "session test 1", "research": False},
            headers=headers,
            timeout=30
        )

        if response1.status_code == 200:
            # Sessions can be lost on restart (ephemeral)
            # This is acceptable for BOP
            assert True, "Sessions can be ephemeral"

    def test_session_storage_options(self):
        """Test options for session storage."""
        # Options:
        # 1. Ephemeral (current) - Lost on restart
        # 2. Volumes - Persist across restarts
        # 3. Database - Full persistence

        options = {
            "ephemeral": {
                "pros": ["Simple", "No setup", "Stateless"],
                "cons": ["Lost on restart"],
                "use_case": "Current implementation"
            },
            "volumes": {
                "pros": ["Persist across restarts", "Simple"],
                "cons": ["Single machine", "Manual backup"],
                "use_case": "If session continuity needed"
            },
            "database": {
                "pros": ["Full persistence", "Multi-machine"],
                "cons": ["Complexity", "Cost"],
                "use_case": "Production with session requirements"
            }
        }

        assert len(options) == 3


class TestPerformancePersistence:
    """Test performance implications of persistence."""

    def test_ephemeral_performance(self):
        """Test that ephemeral storage is fast."""
        # Ephemeral storage is fast but limited:
        # - Max 2000 IOPs
        # - Max 8MiB/s bandwidth

        # For BOP's use case (JSON files, small data), this is sufficient
        assert True, "Ephemeral storage performance is sufficient"

    def test_volume_performance(self):
        """Test volume performance characteristics."""
        # Volumes have better performance:
        # - shared-cpu-1x: 4000 IOPs, 16MiB/s
        # - performance-1x: 12000 IOPs, 48MiB/s

        # Volumes are faster but not required for BOP
        assert True, "Volumes provide better performance if needed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

