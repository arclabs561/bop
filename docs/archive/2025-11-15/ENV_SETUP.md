# Environment Variables Setup

## Auto-Loading

BOP automatically loads environment variables from `.env` file in the repository root when the package is imported.

**Location**: `src/bop/__init__.py`

**Behavior**:
- Automatically finds repo root (looks for `.git`, `.env`, or `pyproject.toml`)
- Loads `.env` from repo root
- Falls back to current directory if repo root not found
- Does not override existing environment variables (respects system/env vars)

## Required Environment Variables

### LLM Backends (at least one required)

```bash
# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini  # Optional, defaults shown

# Anthropic
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-sonnet-4-5  # Optional

# Google / Gemini
GEMINI_API_KEY=your_key_here
# OR
GOOGLE_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-pro  # Optional

# Groq (fastest)
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile  # Optional
```

### Optional Configuration

```bash
# Default backend (auto-detected if not set)
LLM_BACKEND=openai  # Options: openai, anthropic, google, groq
LLM_MODEL=gpt-4o-mini

# BOP features
BOP_USE_CONSTRAINTS=false  # Enable constraint solver
BOP_USE_MUSE_SELECTION=false  # Enable MUSE-based tool selection

# Server configuration
BOP_API_KEY=your_api_key_here
BOP_ALLOW_NO_AUTH=false
BOP_HOST=0.0.0.0
BOP_PORT=8000
BOP_CORS_ORIGINS=*

# MCP tools (optional)
PERPLEXITY_API_KEY=your_key_here
FIRECRAWL_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
KAGI_API_KEY=your_key_here
```

## Setup

1. **Create `.env` file** in repo root:
   ```bash
   cp .env.example .env
   ```

2. **Add your API keys** to `.env`:
   ```bash
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```

3. **That's it!** Variables are auto-loaded when you import `bop`:
   ```python
   import bop  # .env is automatically loaded
   from bop.agent import KnowledgeAgent
   ```

## How It Works

1. When `import bop` is called, `src/bop/__init__.py` runs
2. It finds the repo root by looking for `.git`, `.env`, or `pyproject.toml`
3. Loads `.env` from repo root using `python-dotenv`
4. All subsequent `os.getenv()` calls will use these values

## Notes

- **No manual loading needed**: Just import `bop` and variables are available
- **Respects existing vars**: System/environment variables take precedence
- **Works everywhere**: CLI, server, tests, scripts - all auto-load `.env`
- **Safe**: Fails silently if `.env` doesn't exist (uses defaults)

## Testing

Verify auto-loading works:
```bash
uv run python -c "import bop; import os; print('OPENAI_API_KEY:', bool(os.getenv('OPENAI_API_KEY')))"
```

