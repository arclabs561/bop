"""Tests for multi-backend LLM service support."""

import pytest
from unittest.mock import patch, MagicMock

from bop.llm import LLMService


def test_llm_service_auto_detect_openai():
    """Test auto-detection of OpenAI backend."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel") as mock_model:
            with patch("bop.llm.Agent"):
                service = LLMService()
                assert service.backend == "openai"
                mock_model.assert_called_once()


def test_llm_service_auto_detect_anthropic():
    """Test auto-detection of Anthropic backend."""
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=True):
        with patch("bop.llm.AnthropicModel") as mock_model:
            with patch("bop.llm.Agent"):
                service = LLMService()
                assert service.backend == "anthropic"
                mock_model.assert_called_once()


def test_llm_service_auto_detect_google():
    """Test auto-detection of Google backend."""
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
        with patch("bop.llm.GoogleModel") as mock_model:
            with patch("bop.llm.Agent"):
                service = LLMService()
                assert service.backend == "google"
                mock_model.assert_called_once()


def test_llm_service_explicit_backend():
    """Test explicit backend selection."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"}):
        with patch("bop.llm.AnthropicModel") as mock_model:
            with patch("bop.llm.Agent"):
                service = LLMService(backend="anthropic")
                assert service.backend == "anthropic"
                mock_model.assert_called_once()


def test_llm_service_custom_model_name():
    """Test custom model name."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel") as mock_model:
            with patch("bop.llm.Agent"):
                service = LLMService(backend="openai", model_name="gpt-4o")
                mock_model.assert_called_once_with("gpt-4o")


def test_llm_service_env_backend():
    """Test backend from environment variable."""
    with patch.dict("os.environ", {
        "LLM_BACKEND": "anthropic",
        "ANTHROPIC_API_KEY": "test-key",
    }):
        with patch("bop.llm.AnthropicModel") as mock_model:
            with patch("bop.llm.Agent"):
                service = LLMService()
                assert service.backend == "anthropic"
                mock_model.assert_called_once()


def test_llm_service_env_model():
    """Test model name from environment variable."""
    with patch.dict("os.environ", {
        "OPENAI_API_KEY": "test-key",
        "OPENAI_MODEL": "gpt-4o",
    }):
        with patch("bop.llm.OpenAIChatModel") as mock_model:
            with patch("bop.llm.Agent"):
                service = LLMService(backend="openai")
                mock_model.assert_called_once_with("gpt-4o")


def test_llm_service_no_backend_available():
    """Test error when no backend is available."""
    with patch.dict("os.environ", {}, clear=True):
        with patch("bop.llm.OPENAI_AVAILABLE", False):
            with patch("bop.llm.ANTHROPIC_AVAILABLE", False):
                with patch("bop.llm.GOOGLE_AVAILABLE", False):
                    with pytest.raises(ValueError, match="No LLM backend available"):
                        LLMService()


def test_llm_service_missing_api_key():
    """Test error when API key is missing."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            LLMService(backend="openai")


def test_llm_service_unsupported_backend():
    """Test error for unsupported backend."""
    with pytest.raises(ValueError, match="Unsupported backend"):
        LLMService(backend="unsupported")


def test_llm_service_google_api_key_alternatives():
    """Test Google backend with alternative API key names."""
    # Test GEMINI_API_KEY
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
        with patch("bop.llm.GoogleModel") as mock_model:
            with patch("bop.llm.Agent"):
                service = LLMService(backend="google")
                assert service.backend == "google"
                mock_model.assert_called()

    # Test GOOGLE_API_KEY
    with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}, clear=True):
        with patch("bop.llm.GoogleModel") as mock_model:
            with patch("bop.llm.Agent"):
                service = LLMService(backend="google")
                assert service.backend == "google"
                mock_model.assert_called()


def test_llm_service_groq_backend():
    """Test Groq backend."""
    with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
        with patch("bop.llm.Agent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.model = MagicMock()
            mock_agent_class.return_value = mock_agent
            service = LLMService(backend="groq")
            assert service.backend == "groq"
            # Should use groq: prefix
            mock_agent_class.assert_called()

