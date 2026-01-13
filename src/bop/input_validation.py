"""Input validation and sanitization utilities."""

import logging
import re
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


# Patterns for potentially dangerous input
DANGEROUS_PATTERNS = [
    (r'\.\./', 'path_traversal'),  # Path traversal
    (r'\.\.\\', 'path_traversal_windows'),  # Windows path traversal
    (r'<script', 'xss_script_tag'),  # XSS script tag
    (r'javascript:', 'xss_javascript'),  # XSS javascript: protocol
    (r'on\w+\s*=', 'xss_event_handler'),  # XSS event handlers
    (r'exec\s*\(', 'code_injection_exec'),  # Code injection
    (r'eval\s*\(', 'code_injection_eval'),  # Code injection
    (r'__import__', 'code_injection_import'),  # Code injection
    (r'compile\s*\(', 'code_injection_compile'),  # Code injection
    (r'union\s+select', 'sql_injection'),  # SQL injection (case insensitive)
    (r'drop\s+table', 'sql_injection'),  # SQL injection
    (r';\s*--', 'sql_injection'),  # SQL injection comment
    (r'/\*', 'sql_injection'),  # SQL injection comment
]


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize a string input.

    Args:
        value: Input string
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        ValueError: If input contains dangerous patterns
    """
    if not isinstance(value, str):
        raise ValueError("Input must be a string")

    # Check length
    if max_length and len(value) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length}")

    # Check for dangerous patterns
    for pattern, pattern_name in DANGEROUS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            logger.warning(f"Potentially dangerous input detected: {pattern_name}")
            raise ValueError("Invalid input: potentially dangerous pattern detected")

    # Remove control characters (except newline, tab, carriage return)
    sanitized = ''.join(c for c in value if ord(c) >= 32 or c in '\n\r\t')

    return sanitized


def validate_path(path_str: str, base_path: Optional[Path] = None, allow_absolute: bool = False) -> Path:
    """
    Validate and sanitize a file path.

    Args:
        path_str: Path string to validate
        base_path: Base path to resolve relative paths against
        allow_absolute: Whether to allow absolute paths

    Returns:
        Validated Path object

    Raises:
        ValueError: If path is invalid or dangerous
    """
    if not path_str:
        raise ValueError("Path cannot be empty")

    # Check for path traversal
    if '..' in path_str:
        raise ValueError("Path traversal not allowed")

    # Check for absolute paths if not allowed
    if not allow_absolute and Path(path_str).is_absolute():
        raise ValueError("Absolute paths not allowed")

    # Resolve path
    if base_path:
        resolved = (base_path / path_str).resolve()
        # Ensure resolved path is within base_path
        try:
            resolved.relative_to(base_path.resolve())
        except ValueError:
            raise ValueError("Path outside allowed directory")
        return resolved
    else:
        return Path(path_str).resolve()


def validate_cache_key(key: str, max_length: int = 256) -> str:
    """
    Validate a cache key.

    Args:
        key: Cache key to validate
        max_length: Maximum key length

    Returns:
        Validated key

    Raises:
        ValueError: If key is invalid
    """
    if not key:
        raise ValueError("Cache key cannot be empty")

    if len(key) > max_length:
        raise ValueError(f"Cache key exceeds maximum length of {max_length}")

    # Cache keys should be alphanumeric + some safe characters
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', key):
        raise ValueError("Cache key contains invalid characters")

    return key


def validate_category(category: str, allowed_categories: Optional[List[str]] = None) -> str:
    """
    Validate a cache category.

    Args:
        category: Category to validate
        allowed_categories: List of allowed categories (default: tools, llm, tokens, sessions)

    Returns:
        Validated category

    Raises:
        ValueError: If category is invalid
    """
    if allowed_categories is None:
        allowed_categories = ["tools", "llm", "tokens", "sessions"]

    if category not in allowed_categories:
        raise ValueError(f"Invalid category. Allowed: {', '.join(allowed_categories)}")

    return category


def sanitize_json_input(data: dict, max_depth: int = 10, max_keys: int = 100) -> dict:
    """
    Sanitize JSON input data.

    Args:
        data: Input dictionary
        max_depth: Maximum nesting depth
        max_keys: Maximum number of keys

    Returns:
        Sanitized dictionary

    Raises:
        ValueError: If input is too complex or contains dangerous data
    """
    if not isinstance(data, dict):
        raise ValueError("Input must be a dictionary")

    if len(data) > max_keys:
        raise ValueError(f"Input contains too many keys (max: {max_keys})")

    def _check_depth(obj, depth=0):
        if depth > max_depth:
            raise ValueError(f"Input nesting too deep (max: {max_depth})")
        if isinstance(obj, dict):
            for value in obj.values():
                _check_depth(value, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                _check_depth(item, depth + 1)

    _check_depth(data)

    # Recursively sanitize string values
    def _sanitize_value(value):
        if isinstance(value, str):
            return sanitize_string(value, max_length=10000)
        elif isinstance(value, dict):
            return {k: _sanitize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [_sanitize_value(item) for item in value]
        else:
            return value

    return _sanitize_value(data)

