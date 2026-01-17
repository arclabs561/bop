"""Tests for input validation and sanitization."""

from pathlib import Path

import pytest

from pran.input_validation import (
    sanitize_json_input,
    sanitize_string,
    validate_cache_key,
    validate_category,
    validate_path,
)


class TestSanitizeString:
    """Test string sanitization."""

    def test_basic_sanitization(self):
        """Test basic string sanitization."""
        result = sanitize_string("Hello, world!")
        assert result == "Hello, world!"

    def test_control_characters_removed(self):
        """Test that control characters are removed."""
        result = sanitize_string("Hello\x00world")
        assert "\x00" not in result
        assert "Hello" in result and "world" in result

    def test_newline_tab_preserved(self):
        """Test that newline and tab are preserved."""
        result = sanitize_string("Hello\nworld\t!")
        assert "\n" in result
        assert "\t" in result

    def test_max_length_enforced(self):
        """Test that max length is enforced."""
        with pytest.raises(ValueError, match="exceeds maximum length"):
            sanitize_string("x" * 10001, max_length=10000)

    def test_path_traversal_detected(self):
        """Test that path traversal is detected."""
        with pytest.raises(ValueError, match="dangerous pattern"):
            sanitize_string("../../../etc/passwd")

    def test_xss_script_tag_detected(self):
        """Test that XSS script tags are detected."""
        with pytest.raises(ValueError, match="dangerous pattern"):
            sanitize_string("<script>alert('xss')</script>")

    def test_code_injection_detected(self):
        """Test that code injection is detected."""
        with pytest.raises(ValueError, match="dangerous pattern"):
            sanitize_string("exec('malicious code')")

    def test_sql_injection_detected(self):
        """Test that SQL injection is detected."""
        with pytest.raises(ValueError, match="dangerous pattern"):
            sanitize_string("'; DROP TABLE users; --")


class TestValidatePath:
    """Test path validation."""

    def test_valid_relative_path(self):
        """Test valid relative path."""
        base = Path("/tmp")
        result = validate_path("subdir/file.txt", base_path=base)
        assert result.is_absolute()
        assert "subdir" in str(result)

    def test_path_traversal_rejected(self):
        """Test that path traversal is rejected."""
        base = Path("/tmp")
        with pytest.raises(ValueError, match="Path traversal not allowed"):
            validate_path("../../etc/passwd", base_path=base)

    def test_absolute_path_rejected(self):
        """Test that absolute paths are rejected by default."""
        with pytest.raises(ValueError, match="Absolute paths not allowed"):
            validate_path("/etc/passwd", allow_absolute=False)

    def test_absolute_path_allowed(self):
        """Test that absolute paths can be allowed."""
        result = validate_path("/tmp/test", allow_absolute=True)
        assert result.is_absolute()


class TestValidateCacheKey:
    """Test cache key validation."""

    def test_valid_cache_key(self):
        """Test valid cache key."""
        result = validate_cache_key("test_key_123")
        assert result == "test_key_123"

    def test_invalid_characters_rejected(self):
        """Test that invalid characters are rejected."""
        with pytest.raises(ValueError, match="invalid characters"):
            validate_cache_key("test/key@123")

    def test_max_length_enforced(self):
        """Test that max length is enforced."""
        with pytest.raises(ValueError, match="exceeds maximum length"):
            validate_cache_key("x" * 257, max_length=256)


class TestValidateCategory:
    """Test category validation."""

    def test_valid_category(self):
        """Test valid category."""
        result = validate_category("tools")
        assert result == "tools"

    def test_invalid_category_rejected(self):
        """Test that invalid category is rejected."""
        with pytest.raises(ValueError, match="Invalid category"):
            validate_category("invalid_category")

    def test_custom_allowed_categories(self):
        """Test custom allowed categories."""
        result = validate_category("custom", allowed_categories=["custom", "other"])
        assert result == "custom"


class TestSanitizeJsonInput:
    """Test JSON input sanitization."""

    def test_valid_json(self):
        """Test valid JSON input."""
        data = {"key": "value", "number": 123}
        result = sanitize_json_input(data)
        assert result == data

    def test_too_many_keys_rejected(self):
        """Test that too many keys are rejected."""
        data = {f"key_{i}": f"value_{i}" for i in range(101)}
        with pytest.raises(ValueError, match="too many keys"):
            sanitize_json_input(data, max_keys=100)

    def test_too_deep_nesting_rejected(self):
        """Test that too deep nesting is rejected."""
        data = {"level1": {"level2": {"level3": {"level4": {"level5": {"level6": {"level7": {"level8": {"level9": {"level10": {"level11": "deep"}}}}}}}}}}}
        with pytest.raises(ValueError, match="too deep"):
            sanitize_json_input(data, max_depth=10)

    def test_dangerous_strings_sanitized(self):
        """Test that dangerous strings are sanitized."""
        data = {"message": "<script>alert('xss')</script>"}
        with pytest.raises(ValueError, match="dangerous pattern"):
            sanitize_json_input(data)

