"""BOP: Knowledge Structure Research Agent."""

import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Auto-load .env file from repo root
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Find repo root (look for .git directory or .env file)
def _find_repo_root() -> Path:
    """Find the repository root directory."""
    current = Path(__file__).resolve()
    # Go up from src/bop/__init__.py to find repo root
    for parent in current.parents:
        if (parent / ".git").exists() or (parent / ".env").exists() or (parent / "pyproject.toml").exists():
            return parent
    # Fallback to current working directory
    return Path.cwd()

# Load .env from repo root
_repo_root = _find_repo_root()
_env_path = _repo_root / ".env"
_env_loaded = False

if _env_path.exists():
    load_dotenv(_env_path, override=False)  # Don't override existing env vars
    _env_loaded = True
    logger.debug(f"Loaded .env from {_env_path}")
else:
    # Also try loading from current directory (for backward compatibility)
    _current_env = Path.cwd() / ".env"
    if _current_env.exists():
        load_dotenv(_current_env, override=False)
        _env_loaded = True
        logger.debug(f"Loaded .env from {_current_env}")
    else:
        logger.debug("No .env file found (using system environment variables)")


def validate_env_setup(verbose: bool = False) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validate environment variable setup.
    
    Returns:
        (is_valid, issues_dict) where issues_dict contains:
        - 'missing_required': List of missing required variables
        - 'missing_optional': List of missing optional variables (warnings)
        - 'available': List of available backends/tools
    """
    issues: Dict[str, List[str]] = {
        "missing_required": [],
        "missing_optional": [],
        "available": [],
    }
    
    # Check LLM backends (at least one required)
    llm_backends = {
        "OPENAI_API_KEY": "OpenAI",
        "ANTHROPIC_API_KEY": "Anthropic",
        "GEMINI_API_KEY": "Google/Gemini",
        "GOOGLE_API_KEY": "Google/Gemini",
        "GROQ_API_KEY": "Groq",
    }
    
    has_llm = False
    for key, name in llm_backends.items():
        if os.getenv(key):
            issues["available"].append(f"✅ {name} ({key})")
            has_llm = True
        else:
            if verbose:
                issues["missing_optional"].append(f"⚠️  {name} ({key}) - optional")
    
    if not has_llm:
        issues["missing_required"].append("At least one LLM backend API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, GOOGLE_API_KEY, or GROQ_API_KEY)")
    
    # Check MCP tools (optional)
    mcp_tools = {
        "PERPLEXITY_API_KEY": "Perplexity (deep research)",
        "FIRECRAWL_API_KEY": "Firecrawl (web scraping)",
        "TAVILY_API_KEY": "Tavily (search)",
        "KAGI_API_KEY": "Kagi (search & summarization)",
    }
    
    for key, name in mcp_tools.items():
        if os.getenv(key):
            issues["available"].append(f"✅ {name} ({key})")
        elif verbose:
            issues["missing_optional"].append(f"⚠️  {name} ({key}) - optional")
    
    # Check server config (optional)
    if os.getenv("BOP_API_KEY"):
        issues["available"].append("✅ BOP_API_KEY (server authentication)")
    elif verbose:
        issues["missing_optional"].append("⚠️  BOP_API_KEY - optional (for server auth)")
    
    is_valid = len(issues["missing_required"]) == 0
    
    return is_valid, issues


def get_env_info() -> Dict[str, any]:
    """Get information about environment variable loading."""
    return {
        "env_file_path": str(_env_path) if _env_path.exists() else None,
        "env_loaded": _env_loaded,
        "repo_root": str(_repo_root),
        "has_env_file": _env_path.exists(),
    }


# Validate on import (only log warnings, don't fail)
_is_valid, _issues = validate_env_setup(verbose=False)
if not _is_valid:
    logger.warning(
        f"Missing required environment variables: {', '.join(_issues['missing_required'])}. "
        f"Run 'bop validate-env' for details."
    )

__version__ = "0.1.0"

