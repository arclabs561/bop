"""Test improved error message handling."""

from fastapi import status

from src.bop.error_handling import handle_exception, sanitize_error_message


def test_safe_error_message_returned():
    """Test that safe error messages are returned (not always generic)."""
    # Safe error (validation)
    safe_error = ValueError("Message too long. Maximum length is 10000 characters.")
    sanitized = sanitize_error_message(safe_error)

    # Should return sanitized version, not generic message
    assert sanitized != "An error occurred processing your request."
    assert "message" in sanitized.lower() or "long" in sanitized.lower() or "length" in sanitized.lower()
    assert len(sanitized) <= 200, "Should be limited to 200 chars"


def test_unsafe_error_message_sanitized():
    """Test that unsafe error messages are sanitized."""
    # Unsafe error (contains file path)
    unsafe_error = ValueError("Error in /app/src/bop/server.py line 123")
    sanitized = sanitize_error_message(unsafe_error)

    # Should return generic message
    assert sanitized == "An error occurred processing your request."


def test_error_with_api_key_sanitized():
    """Test that errors containing API keys are sanitized."""
    unsafe_error = ValueError("Invalid API key: tskey-auth-abc123")
    sanitized = sanitize_error_message(unsafe_error)

    # Should return generic message
    assert sanitized == "An error occurred processing your request."


def test_error_message_length_limit():
    """Test that error messages are limited in length."""
    # Very long error message
    long_error = ValueError("A" * 500)
    sanitized = sanitize_error_message(long_error)

    # Should be truncated
    assert len(sanitized) <= 203  # 200 + "..."
    if len(sanitized) > 200:
        assert sanitized.endswith("...")


def test_handle_exception_returns_informative():
    """Test that handle_exception returns informative messages when safe."""
    # Safe validation error
    validation_error = ValueError("Input validation failed: message too long")
    http_exception = handle_exception(validation_error)

    # Should have proper status code
    assert http_exception.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Message should be informative (not just generic)
    assert "invalid" in http_exception.detail.lower() or "validation" in http_exception.detail.lower()
    assert "X-Error-ID" in http_exception.headers


def test_handle_exception_sanitizes_unsafe():
    """Test that handle_exception sanitizes unsafe errors."""
    # Unsafe error
    unsafe_error = ValueError("Error at /app/src/bop/server.py:123")
    http_exception = handle_exception(unsafe_error)

    # Should have generic message
    assert http_exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert http_exception.detail == "An error occurred processing your request."
    assert "X-Error-ID" in http_exception.headers


def test_timeout_error_handling():
    """Test that timeout errors are handled correctly."""
    import asyncio

    timeout_error = asyncio.TimeoutError("Request timed out")
    http_exception = handle_exception(timeout_error)

    assert http_exception.status_code == status.HTTP_504_GATEWAY_TIMEOUT
    assert "timed out" in http_exception.detail.lower() or "timeout" in http_exception.detail.lower()
    assert "X-Error-ID" in http_exception.headers

