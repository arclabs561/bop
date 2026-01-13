"""Tests for LLM provider capabilities."""

from unittest.mock import Mock

import pytest

from bop.llm_capabilities import (
    AnthropicCapabilityAdapter,
    BaseCapabilityAdapter,
    GoogleCapabilityAdapter,
    GroqCapabilityAdapter,
    OpenAICapabilityAdapter,
    create_capability_adapter,
)


class TestBaseCapabilityAdapter:
    """Test base capability adapter."""

    def test_default_capabilities(self):
        """Test default capability detection."""
        model = Mock()
        adapter = BaseCapabilityAdapter(model, "test")

        assert adapter.supports_embeddings is False
        assert adapter.supports_input_params is True

    def test_keyword_similarity(self):
        """Test keyword-based similarity fallback."""
        adapter = BaseCapabilityAdapter(Mock(), "test")

        # Identical texts
        assert adapter._keyword_similarity("hello world", "hello world") == 1.0

        # Similar texts
        sim = adapter._keyword_similarity("hello world", "hello")
        assert 0.0 < sim < 1.0

        # Different texts
        sim = adapter._keyword_similarity("hello", "goodbye")
        assert sim == 0.0

    def test_cosine_similarity(self):
        """Test cosine similarity computation."""
        adapter = BaseCapabilityAdapter(Mock(), "test")

        # Identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        assert adapter._cosine_similarity(vec1, vec2) == 1.0

        # Orthogonal vectors
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        assert adapter._cosine_similarity(vec1, vec2) == 0.0

        # Different vectors
        vec1 = [1.0, 0.0]
        vec2 = [0.5, 0.5]
        sim = adapter._cosine_similarity(vec1, vec2)
        assert 0.0 < sim < 1.0

    @pytest.mark.asyncio
    async def test_compute_similarity_fallback(self):
        """Test similarity computation with fallback."""
        adapter = BaseCapabilityAdapter(Mock(), "test")

        # Should use keyword similarity since embeddings not supported
        sim = await adapter.compute_similarity("hello world", "hello", use_embedding=False)
        assert 0.0 <= sim <= 1.0


class TestOpenAICapabilityAdapter:
    """Test OpenAI capability adapter."""

    def test_vision_detection(self):
        """Test vision capability detection."""
        model = Mock()
        model.model_name = "gpt-4o"
        adapter = OpenAICapabilityAdapter(model)

        assert adapter.supports_vision is True

        model.model_name = "gpt-3.5-turbo"
        adapter = OpenAICapabilityAdapter(model)
        assert adapter.supports_vision is False

    def test_logprobs_support(self):
        """Test logprobs support."""
        model = Mock()
        adapter = OpenAICapabilityAdapter(model)
        assert adapter.supports_logprobs is True

        params = adapter.get_logprob_params()
        assert "logprobs" in params


class TestAnthropicCapabilityAdapter:
    """Test Anthropic capability adapter."""

    def test_vision_detection(self):
        """Test vision capability detection."""
        model = Mock()
        model.model_name = "claude-3-5-sonnet"
        adapter = AnthropicCapabilityAdapter(model)

        assert adapter.supports_vision is True

        model.model_name = "claude-2"
        adapter = AnthropicCapabilityAdapter(model)
        # Claude 2 doesn't have vision in name, but adapter checks for claude-3
        assert adapter.supports_vision is False

    def test_logprobs_support(self):
        """Test logprobs support."""
        model = Mock()
        model.model_name = "claude-3.5-sonnet"
        adapter = AnthropicCapabilityAdapter(model)
        assert adapter.supports_logprobs is True

        model.model_name = "claude-3-opus"
        adapter = AnthropicCapabilityAdapter(model)
        assert adapter.supports_logprobs is False


class TestGoogleCapabilityAdapter:
    """Test Google capability adapter."""

    def test_vision_detection(self):
        """Test vision capability detection."""
        model = Mock()
        model.model_name = "gemini-1.5-pro"
        adapter = GoogleCapabilityAdapter(model)

        assert adapter.supports_vision is True

    def test_logprobs_support(self):
        """Test logprobs support."""
        model = Mock()
        adapter = GoogleCapabilityAdapter(model)
        assert adapter.supports_logprobs is False


class TestCapabilityAdapterFactory:
    """Test capability adapter factory."""

    def test_create_openai_adapter(self):
        """Test creating OpenAI adapter."""
        model = Mock()
        adapter = create_capability_adapter(model, "openai")
        assert isinstance(adapter, OpenAICapabilityAdapter)

    def test_create_anthropic_adapter(self):
        """Test creating Anthropic adapter."""
        model = Mock()
        adapter = create_capability_adapter(model, "anthropic")
        assert isinstance(adapter, AnthropicCapabilityAdapter)

    def test_create_google_adapter(self):
        """Test creating Google adapter."""
        model = Mock()
        adapter = create_capability_adapter(model, "google")
        assert isinstance(adapter, GoogleCapabilityAdapter)

    def test_create_groq_adapter(self):
        """Test creating Groq adapter."""
        model = Mock()
        adapter = create_capability_adapter(model, "groq")
        assert isinstance(adapter, GroqCapabilityAdapter)

    def test_create_unknown_adapter(self):
        """Test creating adapter for unknown backend."""
        model = Mock()
        adapter = create_capability_adapter(model, "unknown")
        assert isinstance(adapter, BaseCapabilityAdapter)


class TestLLMServiceIntegration:
    """Test LLMService integration with capabilities."""

    @pytest.mark.asyncio
    async def test_capability_properties(self):
        """Test that LLMService exposes capability properties."""
        # This would require actual LLM service initialization
        # For now, we test the adapter directly
        from bop.llm import LLMService

        # Mock the service to avoid requiring API keys
        service = Mock(spec=LLMService)
        service.capabilities = OpenAICapabilityAdapter(Mock())

        assert hasattr(service, "supports_embeddings")
        assert hasattr(service, "supports_vision")
        assert hasattr(service, "supports_logprobs")
        assert hasattr(service, "supports_input_params")

