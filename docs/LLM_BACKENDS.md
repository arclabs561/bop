# LLM Backend Support

BOP supports multiple LLM backends through pydantic-ai, allowing you to choose the best provider for your needs.

## Supported Backends

- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4, etc.
- **Anthropic**: Claude Sonnet 4.5, Claude 3.5 Sonnet, etc. (Best quality)
- **Google/Gemini**: Gemini 2.5 Pro, Gemini 1.5 Flash, etc.
- **Groq**: Llama 3.3 70B Versatile, etc. (**Fastest inference** - use for speed-critical operations)

## Configuration

### Environment Variables

Set up your `.env` file with API keys for the backends you want to use:

```bash
# Backend selection (optional - auto-detects if not set)
LLM_BACKEND=openai  # or 'anthropic', 'google', 'groq'
LLM_MODEL=          # Override default model for selected backend

# OpenAI
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini

# Anthropic
ANTHROPIC_API_KEY=your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-5

# Google/Gemini
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-2.5-pro
# OR
GOOGLE_API_KEY=your-key-here
GOOGLE_MODEL=gemini-2.5-pro

# Groq
GROQ_API_KEY=your-key-here
GROQ_MODEL=llama-3.3-70b-versatile
```

### Installation

Install pydantic-ai with the backends you need:

```bash
# OpenAI only
uv sync --extra llm-openai

# Anthropic only
uv sync --extra llm-anthropic

# Google only
uv sync --extra llm-google

# All backends
uv sync --extra llm-all
```

## Usage

### Auto-Detection

If `LLM_BACKEND` is not set, BOP will auto-detect from available API keys in this order:
1. **Groq** (if `GROQ_API_KEY` is set) - **Fastest inference, prioritized for speed**
2. Anthropic (if `ANTHROPIC_API_KEY` is set) - Best quality
3. OpenAI (if `OPENAI_API_KEY` is set)
4. Google (if `GEMINI_API_KEY` or `GOOGLE_API_KEY` is set)

**Note**: Groq is prioritized for auto-detection because it provides the fastest inference. For quality-critical operations, explicitly set `LLM_BACKEND=anthropic` or `LLM_BACKEND=openai`.

### Explicit Selection

```python
from bop.llm import LLMService

# Use specific backend
service = LLMService(backend="anthropic")

# Use specific backend and model
service = LLMService(backend="google", model_name="gemini-1.5-flash")
```

### Programmatic Selection

```python
from bop.agent import KnowledgeAgent
from bop.llm import LLMService

# Create agent with specific LLM backend
llm_service = LLMService(backend="anthropic")
agent = KnowledgeAgent(llm_service=llm_service)
```

## Model Names

### OpenAI
- `gpt-4o`, `gpt-4o-mini`
- `gpt-4-turbo`, `gpt-4`
- `gpt-3.5-turbo`

### Anthropic
- `claude-sonnet-4-5`
- `claude-3-5-sonnet-latest`
- `claude-3-opus-latest`
- `claude-3-haiku-latest`

### Google/Gemini
- `gemini-2.5-pro`
- `gemini-1.5-pro`
- `gemini-1.5-flash`

### Groq
- `llama-3.3-70b-versatile`
- `llama-3.1-70b-versatile`
- `mixtral-8x7b-32768`

## Examples

### Using OpenAI

```bash
export OPENAI_API_KEY=your-key
export LLM_BACKEND=openai
uv run bop chat
```

### Using Anthropic

```bash
export ANTHROPIC_API_KEY=your-key
export LLM_BACKEND=anthropic
uv run bop chat
```

### Using Google Gemini

```bash
export GEMINI_API_KEY=your-key
export LLM_BACKEND=google
uv run bop chat
```

### Using Groq

```bash
export GROQ_API_KEY=your-key
export LLM_BACKEND=groq
uv run bop chat
```

## Fallback Behavior

If a backend is not available or API key is missing:
- The service will raise a clear error message
- The agent will continue without LLM (using fallback heuristics)
- All LLM-dependent features will gracefully degrade

## Provider Capabilities

BOP provides a unified interface for checking and using provider-specific capabilities:

- **Embeddings**: Semantic similarity computation (with keyword fallback)
- **Vision**: Image input support detection
- **Logprobs**: Log probability parameter support
- **Input Parameters**: Custom parameter availability

### Checking Capabilities

```python
from bop.llm import LLMService

service = LLMService()

# Check capabilities
if service.supports_vision:
    image_types = service.get_vision_input_types()
    # ['image/jpeg', 'image/png', 'image/webp']

if service.supports_logprobs:
    params = service.get_logprob_params()
    # {'logprobs': 'bool or int (0-5)', ...}

# Get comprehensive capability info
info = service.get_capability_info()
# {
#   'backend': 'openai',
#   'supports_embeddings': False,
#   'supports_vision': True,
#   'supports_logprobs': True,
#   ...
# }
```

### Semantic Similarity

The `compute_similarity` method is used internally for belief alignment and can be used directly:

```python
similarity = await service.compute_similarity(
    "I think trust is important",
    "Trust is crucial for systems"
)
# Returns: 0.0 to 1.0 similarity score
# Uses embeddings if available, falls back to keyword matching
```

See `docs/LLM_CAPABILITIES.md` for detailed capability documentation.

## Testing

Tests are available for all backends:

```bash
# Test multi-backend support
uv run pytest tests/test_llm_multi_backend.py -v

# Test with specific backend
LLM_BACKEND=anthropic uv run pytest tests/test_llm.py -v

# Test capabilities
uv run pytest tests/test_llm_capabilities.py -v

# Test capabilities integration
uv run pytest tests/test_llm_capabilities_integration.py -v
```

