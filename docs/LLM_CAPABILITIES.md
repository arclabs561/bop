# LLM Provider Capabilities Protocol

This document describes the LLM provider capabilities protocol and how to use it for provider-agnostic feature detection and usage.

## Overview

Different LLM providers support different capabilities:
- **Embeddings**: Generate vector embeddings for semantic similarity
- **Vision**: Process image inputs alongside text
- **Logprobs**: Return log probabilities for tokens
- **Input Parameters**: Custom parameters (temperature, max_tokens, etc.)

The capabilities protocol provides a unified interface to check and use these features across different providers (OpenAI, Anthropic, Google, Groq) without provider-specific code.

## Architecture

### Protocol Definition

The `LLMProviderCapabilities` protocol defines the interface:

```python
@runtime_checkable
class LLMProviderCapabilities(Protocol):
    supports_embeddings: bool
    supports_vision: bool
    supports_logprobs: bool
    supports_input_params: bool
    
    async def generate_embedding(text: str) -> List[float]
    async def compute_similarity(text1: str, text2: str) -> float
    def get_vision_input_types() -> List[str]
    def get_logprob_params() -> Dict[str, Any]
    def get_custom_input_params() -> Dict[str, Any]
```

### Capability Adapters

Provider-specific adapters implement the protocol:

- `OpenAICapabilityAdapter`: OpenAI-specific capabilities
- `AnthropicCapabilityAdapter`: Anthropic-specific capabilities
- `GoogleCapabilityAdapter`: Google/Gemini-specific capabilities
- `GroqCapabilityAdapter`: Groq-specific capabilities
- `BaseCapabilityAdapter`: Fallback with sensible defaults

## Usage

### Basic Capability Checking

```python
from bop.llm import LLMService

# Initialize service (auto-detects backend)
service = LLMService()

# Check capabilities
if service.supports_embeddings:
    embedding = await service.generate_embedding("Hello world")
    
if service.supports_vision:
    image_types = service.get_vision_input_types()
    # ['image/jpeg', 'image/png', 'image/webp']
    
if service.supports_logprobs:
    params = service.get_logprob_params()
    # {'logprobs': 'bool or int (0-5)', 'top_logprobs': 'int (0-20, optional)'}
```

### Semantic Similarity

The `compute_similarity` method is used by the orchestrator for belief alignment:

```python
from bop.llm import LLMService

service = LLMService()

# Compute similarity (uses embeddings if available, falls back to keyword matching)
similarity = await service.compute_similarity(
    "I think trust is important",
    "Trust is crucial for systems"
)
# Returns: 0.0 to 1.0 similarity score
```

This method:
1. Tries to use embeddings if `supports_embeddings` is True
2. Falls back to keyword-based Jaccard similarity if embeddings unavailable
3. Always returns a value between 0.0 and 1.0

### Provider-Specific Behavior

#### OpenAI
- **Vision**: Supported in `gpt-4o`, `gpt-4-turbo`, `gpt-4-vision`
- **Logprobs**: Supported (with `logprobs` and `top_logprobs` parameters)
- **Embeddings**: Not available via chat API (would need separate OpenAI client)

#### Anthropic
- **Vision**: Supported in `claude-3` and `claude-sonnet-4` models
- **Logprobs**: Supported in `claude-3.5` and `claude-sonnet-4` models
- **Embeddings**: Not available via chat API

#### Google/Gemini
- **Vision**: Supported in all Gemini models
- **Logprobs**: Not exposed via standard API
- **Embeddings**: Available via separate embedding models (would need separate client)

#### Groq
- **Vision**: Typically not supported
- **Logprobs**: May vary by model
- **Embeddings**: Not provided

## Integration with Existing Code

### Orchestrator Integration

The orchestrator's `_compute_semantic_alignment` method now works properly:

```python
# In orchestrator.py
if self.llm_service and hasattr(self.llm_service, 'compute_similarity'):
    similarity = await self.llm_service.compute_similarity(belief_text, evidence_text)
```

This check now works because `LLMService` implements `compute_similarity` via the capabilities protocol.

### Adding New Capabilities

To add support for a new capability:

1. **Add to Protocol**: Update `LLMProviderCapabilities` protocol
2. **Implement in Base Adapter**: Add default implementation in `BaseCapabilityAdapter`
3. **Provider-Specific**: Override in provider-specific adapters if needed
4. **Expose in LLMService**: Add method/property to `LLMService` that delegates to adapter

Example:

```python
# In llm_capabilities.py
@runtime_checkable
class LLMProviderCapabilities(Protocol):
    @property
    def supports_streaming(self) -> bool:
        """Whether provider supports streaming responses."""
        ...

# In BaseCapabilityAdapter
@property
def supports_streaming(self) -> bool:
    """Default: most providers support streaming."""
    return True

# In LLMService
@property
def supports_streaming(self) -> bool:
    return self.capabilities.supports_streaming
```

## Testing

Tests are in `tests/test_llm_capabilities.py`:

- Capability detection for each provider
- Similarity computation (cosine and keyword fallback)
- Adapter factory function
- Integration with LLMService

Run tests:

```bash
uv run pytest tests/test_llm_capabilities.py -v
```

## Benefits

1. **Provider Agnostic**: Write code once, works with any provider
2. **Graceful Degradation**: Fallbacks when capabilities unavailable
3. **Type Safety**: Protocol ensures consistent interface
4. **Extensible**: Easy to add new capabilities or providers
5. **Clear Documentation**: Capability methods document what's available

## Future Enhancements

Potential additions:

- **Streaming**: Protocol for streaming responses
- **Function Calling**: Protocol for tool/function calling capabilities
- **Rate Limits**: Protocol for rate limit information
- **Cost Tracking**: Protocol for cost estimation
- **Embedding Integration**: Direct integration with provider embedding APIs

