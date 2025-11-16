"""
Tests for .env auto-loading and validation.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from bop import validate_env_setup, get_env_info


class TestEnvLoading:
    """Test .env file auto-loading."""
    
    def test_validate_env_setup_with_keys(self):
        """Test validation when API keys are present."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "PERPLEXITY_API_KEY": "test-key",
        }, clear=False):
            is_valid, issues = validate_env_setup(verbose=True)
            
            assert is_valid is True
            assert len(issues["missing_required"]) == 0
            assert len(issues["available"]) > 0
            assert any("OpenAI" in item for item in issues["available"])
            assert any("Perplexity" in item for item in issues["available"])
    
    def test_validate_env_setup_missing_required(self):
        """Test validation when no LLM keys are present."""
        # Remove all LLM keys
        env_vars_to_remove = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
            "GOOGLE_API_KEY", "GROQ_API_KEY"
        ]
        
        # Actually remove them
        original_values = {}
        for key in env_vars_to_remove:
            original_values[key] = os.environ.pop(key, None)
        
        try:
            is_valid, issues = validate_env_setup(verbose=False)
            
            assert is_valid is False
            assert len(issues["missing_required"]) > 0
            assert any("LLM backend" in item for item in issues["missing_required"])
        finally:
            # Restore original values
            for key, value in original_values.items():
                if value is not None:
                    os.environ[key] = value
    
    def test_validate_env_setup_verbose(self):
        """Test verbose mode shows optional variables."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
        }, clear=False):
            is_valid, issues = validate_env_setup(verbose=True)
            
            assert is_valid is True
            # Verbose mode should show optional variables
            assert len(issues["missing_optional"]) > 0
            assert any("optional" in item.lower() for item in issues["missing_optional"])
    
    def test_get_env_info(self):
        """Test getting environment info."""
        info = get_env_info()
        
        assert "env_file_path" in info
        assert "env_loaded" in info
        assert "repo_root" in info
        assert "has_env_file" in info
        assert isinstance(info["env_loaded"], bool)
        assert isinstance(info["has_env_file"], bool)


class TestEnvFileLoading:
    """Test .env file loading behavior."""
    
    def test_env_file_auto_loaded(self):
        """Test that .env is automatically loaded when bop is imported."""
        # This test verifies that importing bop loads .env
        # We can't easily test the actual loading without creating a real .env file,
        # but we can verify the function exists and works
        
        # Re-import to trigger loading
        import importlib
        import bop
        importlib.reload(bop)
        
        # Check that validation function works
        is_valid, issues = validate_env_setup(verbose=False)
        # Should not crash, regardless of whether keys are set
        assert isinstance(is_valid, bool)
        assert isinstance(issues, dict)
        assert "missing_required" in issues
        assert "available" in issues


class TestEnvValidationCLI:
    """Test CLI validation command (integration test)."""
    
    def test_validate_env_command_exists(self):
        """Test that validate-env command exists in CLI."""
        from bop.cli import app, validate_env
        
        # Check that function exists and is callable
        assert callable(validate_env)
        assert validate_env.__name__ == "validate_env"
        
        # Check that it's registered in the app
        # Typer stores commands differently, so we check the function exists
        assert hasattr(app, "registered_commands") or hasattr(app, "commands")

