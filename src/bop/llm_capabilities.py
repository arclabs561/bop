"""LLM provider capabilities protocol and implementations.

This module defines a protocol for LLM provider capabilities (embeddings, vision, logprobs, etc.)
and provides capability detection and provider-specific implementations.
"""

import logging
from abc import ABC
from typing import Any, Dict, List, Protocol

try:
    from typing_extensions import runtime_checkable
except ImportError:
    # Python 3.12+ has runtime_checkable in typing
    from typing import runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMProviderCapabilities(Protocol):
    """Protocol defining LLM provider capabilities.

    This protocol allows checking and using provider-specific features
    in a provider-agnostic way.
    """

    @property
    def supports_embeddings(self) -> bool:
        """Whether the provider supports embedding generation."""
        ...

    @property
    def supports_vision(self) -> bool:
        """Whether the provider supports vision/image inputs."""
        ...

    @property
    def supports_logprobs(self) -> bool:
        """Whether the provider supports log probability returns."""
        ...

    @property
    def supports_input_params(self) -> bool:
        """Whether the provider supports custom input parameters."""
        ...

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector as list of floats

        Raises:
            NotImplementedError: If embeddings not supported
        """
        ...

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple texts.

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors

        Raises:
            NotImplementedError: If embeddings not supported
        """
        ...

    async def compute_similarity(
        self, text1: str, text2: str, use_embedding: bool = True
    ) -> float:
        """Compute semantic similarity between two texts.

        Args:
            text1: First text
            text2: Second text
            use_embedding: Whether to use embeddings (if available) or fallback method

        Returns:
            Similarity score between 0.0 and 1.0
        """
        ...

    def get_vision_input_types(self) -> List[str]:
        """Get supported vision input types (e.g., 'image/jpeg', 'image/png').

        Returns:
            List of supported MIME types
        """
        ...

    def get_logprob_params(self) -> Dict[str, Any]:
        """Get parameters needed for logprob requests.

        Returns:
            Dictionary of parameter names and their types/requirements
        """
        ...

    def get_custom_input_params(self) -> Dict[str, Any]:
        """Get custom input parameters supported by the provider.

        Returns:
            Dictionary of parameter names and their types/requirements
        """
        ...


class BaseCapabilityAdapter(ABC):
    """Base adapter for LLM provider capabilities.

    Provides default implementations and fallback behavior.
    """

    def __init__(self, model: Any, backend: str):
        """Initialize capability adapter.

        Args:
            model: The underlying model instance
            backend: Backend name (e.g., 'openai', 'anthropic', 'google')
        """
        self.model = model
        self.backend = backend

    @property
    def supports_embeddings(self) -> bool:
        """Default: embeddings not supported."""
        return False

    @property
    def supports_vision(self) -> bool:
        """Default: check based on backend and model name."""
        # Most modern models support vision
        vision_models = {
            "openai": ["gpt-4o", "gpt-4-turbo", "gpt-4-vision"],
            "anthropic": ["claude-3", "claude-sonnet-4"],
            "google": ["gemini-1.5", "gemini-2.5"],
        }
        if self.backend in vision_models:
            model_name = getattr(self.model, "model_name", "") or str(self.model)
            return any(vm in model_name.lower() for vm in vision_models[self.backend])
        return False

    @property
    def supports_logprobs(self) -> bool:
        """Default: check based on backend."""
        # OpenAI and Anthropic support logprobs
        return self.backend in ("openai", "anthropic")

    @property
    def supports_input_params(self) -> bool:
        """Default: most providers support some custom params."""
        return True

    async def generate_embedding(self, text: str) -> List[float]:
        """Default: raise NotImplementedError."""
        raise NotImplementedError(
            f"Embeddings not supported for {self.backend} backend"
        )

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Default: batch embedding generation."""
        return [await self.generate_embedding(text) for text in texts]

    async def compute_similarity(
        self, text1: str, text2: str, use_embedding: bool = True
    ) -> float:
        """Compute similarity with embedding fallback to keyword matching."""
        if use_embedding and self.supports_embeddings:
            try:
                emb1 = await self.generate_embedding(text1)
                emb2 = await self.generate_embedding(text2)
                return self._cosine_similarity(emb1, emb2)
            except Exception as e:
                logger.debug(f"Embedding similarity failed: {e}, using fallback")
                return self._keyword_similarity(text1, text2)
        else:
            return self._keyword_similarity(text1, text2)

    def get_vision_input_types(self) -> List[str]:
        """Default: common image types."""
        if self.supports_vision:
            return ["image/jpeg", "image/png", "image/webp"]
        return []

    def get_logprob_params(self) -> Dict[str, Any]:
        """Default: empty if not supported."""
        if self.supports_logprobs:
            return {
                "logprobs": "int or bool",
                "top_logprobs": "int (optional)",
            }
        return {}

    def get_custom_input_params(self) -> Dict[str, Any]:
        """Default: common parameters."""
        params = {
            "temperature": "float (0.0-2.0)",
            "max_tokens": "int",
            "top_p": "float (0.0-1.0)",
        }
        if self.backend == "openai":
            params.update({
                "frequency_penalty": "float (-2.0 to 2.0)",
                "presence_penalty": "float (-2.0 to 2.0)",
            })
        elif self.backend == "anthropic":
            params.update({
                "stop_sequences": "List[str]",
            })
        return params

    def get_capability_info(self) -> Dict[str, Any]:
        """Get comprehensive capability information for debugging/inspection.

        Returns:
            Dictionary with capability flags and details
        """
        return {
            "backend": self.backend,
            "supports_embeddings": self.supports_embeddings,
            "supports_vision": self.supports_vision,
            "supports_logprobs": self.supports_logprobs,
            "supports_input_params": self.supports_input_params,
            "vision_input_types": self.get_vision_input_types(),
            "logprob_params": self.get_logprob_params(),
            "custom_input_params": list(self.get_custom_input_params().keys()),
        }

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import math

        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same length")

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    @staticmethod
    def _keyword_similarity(text1: str, text2: str) -> float:
        """Fallback keyword-based similarity (Jaccard similarity)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0


class OpenAICapabilityAdapter(BaseCapabilityAdapter):
    """OpenAI-specific capability adapter."""

    def __init__(self, model: Any):
        """Initialize OpenAI adapter."""
        super().__init__(model, "openai")
        self._model_name = getattr(model, "model_name", "") or str(model)

    @property
    def supports_embeddings(self) -> bool:
        """OpenAI has separate embedding models."""
        # OpenAI has text-embedding models, but not via chat API
        # For now, we'd need to use OpenAI's embeddings API separately
        return False  # Would need separate OpenAI client

    @property
    def supports_vision(self) -> bool:
        """OpenAI vision models support images."""
        vision_models = ["gpt-4o", "gpt-4-turbo", "gpt-4-vision"]
        return any(vm in self._model_name.lower() for vm in vision_models)

    @property
    def supports_logprobs(self) -> bool:
        """OpenAI supports logprobs."""
        return True

    def get_logprob_params(self) -> Dict[str, Any]:
        """OpenAI logprob parameters."""
        return {
            "logprobs": "bool or int (0-5)",
            "top_logprobs": "int (0-20, optional)",
        }


class AnthropicCapabilityAdapter(BaseCapabilityAdapter):
    """Anthropic-specific capability adapter."""

    def __init__(self, model: Any):
        """Initialize Anthropic adapter."""
        super().__init__(model, "anthropic")
        self._model_name = getattr(model, "model_name", "") or str(model)

    @property
    def supports_embeddings(self) -> bool:
        """Anthropic doesn't expose embeddings via chat API."""
        return False

    @property
    def supports_vision(self) -> bool:
        """Claude 3+ models support vision."""
        return "claude-3" in self._model_name.lower() or "claude-sonnet-4" in self._model_name.lower()

    @property
    def supports_logprobs(self) -> bool:
        """Anthropic supports logprobs in some models."""
        # Claude 3.5+ supports logprobs
        return "claude-3.5" in self._model_name.lower() or "claude-sonnet-4" in self._model_name.lower()


class GoogleCapabilityAdapter(BaseCapabilityAdapter):
    """Google/Gemini-specific capability adapter."""

    def __init__(self, model: Any):
        """Initialize Google adapter."""
        super().__init__(model, "google")
        self._model_name = getattr(model, "model_name", "") or str(model)

    @property
    def supports_embeddings(self) -> bool:
        """Gemini has embedding models."""
        # Would need to use google-generativeai directly
        return False  # Would need separate client

    @property
    def supports_vision(self) -> bool:
        """Gemini models support vision."""
        return "gemini" in self._model_name.lower()

    @property
    def supports_logprobs(self) -> bool:
        """Gemini doesn't expose logprobs via standard API."""
        return False


class GroqCapabilityAdapter(BaseCapabilityAdapter):
    """Groq-specific capability adapter."""

    def __init__(self, model: Any):
        """Initialize Groq adapter."""
        super().__init__(model, "groq")

    @property
    def supports_embeddings(self) -> bool:
        """Groq doesn't provide embeddings."""
        return False

    @property
    def supports_vision(self) -> bool:
        """Groq models typically don't support vision."""
        return False

    @property
    def supports_logprobs(self) -> bool:
        """Groq may support logprobs depending on model."""
        return False


def create_capability_adapter(model: Any, backend: str) -> BaseCapabilityAdapter:
    """Create appropriate capability adapter for backend.

    Args:
        model: The model instance
        backend: Backend name ('openai', 'anthropic', 'google', 'groq')

    Returns:
        Capability adapter instance
    """
    adapters = {
        "openai": OpenAICapabilityAdapter,
        "anthropic": AnthropicCapabilityAdapter,
        "google": GoogleCapabilityAdapter,
        "groq": GroqCapabilityAdapter,
    }

    adapter_class = adapters.get(backend)
    if adapter_class:
        return adapter_class(model)
    else:
        # Fallback to base adapter with backend
        return BaseCapabilityAdapter(model, backend)

