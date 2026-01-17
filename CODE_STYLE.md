# Code Style Guide

## Comment Style

BOP follows a consistent comment style throughout the codebase.

### Module-Level Docstrings

Use triple-quoted docstrings for module documentation:

```python
"""Brief description of the module's purpose.

Optional longer description if needed.
"""
```

**Example**:
```python
"""Hierarchical session-based persistence for learning data with advanced features."""
```

### Class Docstrings

Use triple-quoted docstrings for class documentation:

```python
class MyClass:
    """Brief description of the class.
    
    Optional longer description explaining the class's purpose,
    key features, and usage patterns.
    
    Attributes:
        attr1: Description of attribute
        attr2: Description of attribute
    """
```

**Example**:
```python
class KnowledgeAgent:
    """Main agent for knowledge structure research and interaction."""
```

### Function/Method Docstrings

Use triple-quoted docstrings with Args and Returns sections:

```python
def my_function(arg1: str, arg2: int) -> Dict[str, Any]:
    """Brief description of the function.
    
    Optional longer description explaining what the function does,
    any important behavior, or edge cases.
    
    Args:
        arg1: Description of argument
        arg2: Description of argument
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When invalid input is provided
    """
```

**Example**:
```python
async def chat(
    self,
    message: str,
    use_schema: Optional[str] = None,
    use_research: bool = False,
) -> Dict[str, Any]:
    """
    Process a chat message and generate response.

    Args:
        message: User message
        use_schema: Optional schema name to use for structured reasoning
        use_research: Whether to conduct deep research

    Returns:
        Response dictionary
    """
```

### Section Dividers

Use comment dividers to organize large files:

```python
# ============================================================================
# Section Name
# ============================================================================
```

**Example**:
```python
# ============================================================================
# Data Models
# ============================================================================

@dataclass
class EvaluationEntry:
    """A single evaluation entry within a session."""
    # ...
```

### Inline Comments

Use `#` for inline comments explaining non-obvious code:

```python
# LLMService will auto-detect backend from environment
self.llm_service = LLMService()

# If research fails, continue without it
response["research_conducted"] = False
```

**Guidelines**:
- Explain **why**, not **what** (code should be self-documenting)
- Use comments for non-obvious behavior, edge cases, or workarounds
- Keep comments concise and clear
- Update comments when code changes

### Type Hints

Always use type hints for function signatures:

```python
def process_data(
    data: List[Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Process data with optional configuration."""
    # ...
```

### Constants

Use UPPER_SNAKE_CASE for constants with descriptive comments:

```python
# Default inactivity timeout (1 hour)
DEFAULT_INACTIVITY_TIMEOUT = 3600.0

# Mbopmum number of tools per subproblem
MAX_TOOLS_PER_SUBPROBLEM = 2
```

## Code Organization

### Imports

Organize imports in this order:
1. Standard library
2. Third-party packages
3. Local application imports

```python
# Standard library
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Third-party
import typer
from rich.console import Console
from pydantic import BaseModel

# Local
from .agent import KnowledgeAgent
from .schemas import get_schema
```

### File Structure

Organize files with clear sections:

```python
"""Module docstring."""

# Imports
# ...

# Constants
# ...

# ============================================================================
# Section 1
# ============================================================================

# Classes/functions for section 1

# ============================================================================
# Section 2
# ============================================================================

# Classes/functions for section 2
```

## Naming Conventions

- **Classes**: `PascalCase` (e.g., `KnowledgeAgent`)
- **Functions/Methods**: `snake_case` (e.g., `process_message`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)
- **Private**: Prefix with `_` (e.g., `_internal_method`)
- **Type Variables**: `PascalCase` (e.g., `T`, `ResponseType`)

## Formatting

- **Line Length**: 100 characters (configured in `ruff`)
- **Indentation**: 4 spaces
- **Quotes**: Prefer double quotes for strings, single quotes for characters
- **Trailing Commas**: Use in multi-line structures

## See Also

- `pyproject.toml` - Ruff and mypy configuration
- `CONTRIBUTING.md` - Development guidelines

