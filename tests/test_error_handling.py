"""Tests for enhanced error handling."""

import pytest
from fastapi import FastAPI, HTTPException, status

from bop.error_handling import (
    create_error_response,
    handle_exception,
    sanitize_error_message,
)


@pytest.fixture
def test_app():
    """Create a test FastAPI app."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error with /app/path")

    @app.get("/api-key-error")
    async def api_key_error():
        raise ValueError("Invalid API key: abc123")

    @app.get("/timeout-error")
    async def timeout_error():
        raise TimeoutError("Request timed out")

    return app


class TestErrorSanitization:
    """Test error message sanitization."""

    def test_sanitize_file_paths(self):
        """Test that file paths are sanitized."""
        error = ValueError("Error in /app/src/server.py line 123")
        sanitized = sanitize_error_message(error)
        assert "/app/" not in sanitized
        assert "file" not in sanitized.lower()
        assert sanitized == "An error occurred processing your request."

    def test_sanitize_api_keys(self):
        """Test that API keys are sanitized."""
        error = ValueError("Invalid API key: abc123def456")
        sanitized = sanitize_error_message(error)
        assert "api_key" not in sanitized.lower()
        assert "abc123" not in sanitized
        assert sanitized == "An error occurred processing your request."

    def test_sanitize_stack_traces(self):
        """Test that stack traces are sanitized."""
        error = ValueError("Traceback (most recent call last):\n  File \"/app/server.py\", line 1")
        sanitized = sanitize_error_message(error)
        assert "traceback" not in sanitized.lower()
        assert "file" not in sanitized.lower()
        assert sanitized == "An error occurred processing your request."

    def test_sanitize_passwords(self):
        """Test that passwords are sanitized."""
        error = ValueError("Invalid password: secret123")
        sanitized = sanitize_error_message(error)
        assert "password" not in sanitized.lower()
        assert "secret" not in sanitized.lower()
        assert sanitized == "An error occurred processing your request."


class TestErrorHandling:
    """Test error handling."""

    def test_handle_exception_creates_error_id(self):
        """Test that handle_exception creates error IDs."""
        error = ValueError("Test error")
        http_exception = handle_exception(error)

        assert isinstance(http_exception, HTTPException)
        assert "X-Error-ID" in http_exception.headers
        assert http_exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_handle_timeout_error(self):
        """Test that timeout errors are handled correctly."""
        error = TimeoutError("Request timed out")
        http_exception = handle_exception(error)

        assert http_exception.status_code == status.HTTP_504_GATEWAY_TIMEOUT
        assert "timed out" in http_exception.detail.lower()
        assert "X-Error-ID" in http_exception.headers

    def test_handle_authentication_error(self):
        """Test that authentication errors are handled correctly."""
        error = ValueError("Invalid API key")
        http_exception = handle_exception(error)

        assert http_exception.status_code == status.HTTP_401_UNAUTHORIZED
        assert "authentication" in http_exception.detail.lower() or "api key" in http_exception.detail.lower()
        assert "X-Error-ID" in http_exception.headers

    def test_handle_http_exception_preserves_status(self):
        """Test that HTTPException status codes are preserved."""
        original = HTTPException(status_code=404, detail="Not found")
        http_exception = handle_exception(original)

        assert http_exception.status_code == 404
        # Message should be sanitized
        assert "X-Error-ID" in http_exception.headers


class TestErrorResponse:
    """Test error response creation."""

    def test_create_error_response(self):
        """Test creating error responses."""
        response = create_error_response(
            status_code=500,
            detail="Test error",
            error_type="test_error",
        )

        assert response.status_code == 500
        data = response.body.decode()
        assert "error" in data
        assert "id" in data
        assert "X-Error-ID" in response.headers

    def test_error_response_with_additional_data(self):
        """Test error response with additional data."""
        response = create_error_response(
            status_code=400,
            detail="Validation error",
            additional_data={"field": "message", "value": "invalid"},
        )

        data = response.body.decode()
        assert "error" in data
        assert "data" in data
        assert "field" in data

