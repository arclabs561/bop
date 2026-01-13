"""Enhanced error handling with error IDs and structured logging."""

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

# Import get_request_id from server_context
try:
    from .server_context import get_request_id
except ImportError:
    def get_request_id() -> Optional[str]:
        return None

logger = logging.getLogger(__name__)


class ErrorIDMiddleware:
    """Add error IDs to error responses for tracking."""

    @staticmethod
    def add_error_id_to_response(response: JSONResponse, error_id: str):
        """Add error ID to response headers."""
        response.headers["X-Error-ID"] = error_id
        return response


def create_error_response(
    status_code: int,
    detail: str,
    error_id: Optional[str] = None,
    error_type: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """
    Create a standardized error response with error ID.

    Args:
        status_code: HTTP status code
        detail: Error message (sanitized)
        error_id: Optional error ID (generated if not provided)
        error_type: Optional error type/category
        additional_data: Optional additional error data

    Returns:
        JSONResponse with error details
    """
    if error_id is None:
        error_id = str(uuid.uuid4())

    error_response = {
        "error": {
            "id": error_id,
            "message": detail,
            "status_code": status_code,
        }
    }

    if error_type:
        error_response["error"]["type"] = error_type

    if additional_data:
        error_response["error"]["data"] = additional_data

    response = JSONResponse(
        status_code=status_code,
        content=error_response,
    )

    # Add error ID to headers
    response.headers["X-Error-ID"] = error_id

    return response


def sanitize_error_message(error: Exception, default_message: str = "An error occurred processing your request.") -> str:
    """
    Sanitize error messages to prevent information disclosure.

    Args:
        error: The exception that occurred
        default_message: Default message if error can't be safely exposed

    Returns:
        Sanitized error message
    """
    error_str = str(error).lower()

    # Never expose these patterns
    sensitive_patterns = [
        "api_key",
        "api key",
        "password",
        "secret",
        "token",
        "credential",
        "file://",
        "/app/",
        "/usr/",
        "/var/",
        "traceback",
        "stack trace",
        "exception",
        "error at",
    ]

    for pattern in sensitive_patterns:
        if pattern in error_str:
            return default_message

    # Check for file paths
    if "/" in str(error) and any(part in str(error) for part in ["app", "usr", "var", "home", "root"]):
        return default_message

    # Check for stack trace indicators
    if "traceback" in error_str or "file \"" in error_str or "line " in error_str:
        return default_message

    # If we get here, the error message seems safe
    # Return a sanitized version of the error message (not the full default)
    # This helps users understand what went wrong while still being safe
    error_msg = str(error)
    # Limit length to prevent DoS
    if len(error_msg) > 200:
        error_msg = error_msg[:200] + "..."
    return error_msg


def handle_exception(
    error: Exception,
    request_id: Optional[str] = None,
    default_message: str = "An error occurred processing your request.",
) -> HTTPException:
    """
    Handle exceptions and create sanitized HTTP exceptions.

    Args:
        error: The exception that occurred
        request_id: Optional request ID for logging
        default_message: Default error message

    Returns:
        HTTPException with sanitized message
    """
    error_id = str(uuid.uuid4())
    sanitized_message = sanitize_error_message(error, default_message)

    # Log the actual error with error ID
    logger.error(
        f"Error {error_id} (request {request_id}): {error}",
        exc_info=True,
        extra={"error_id": error_id, "request_id": request_id},
    )

    # Determine status code based on error type
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(error, HTTPException):
        status_code = error.status_code
        # Use sanitized message instead of original
        return HTTPException(
            status_code=status_code,
            detail=sanitized_message,
            headers={"X-Error-ID": error_id},
        )
    elif isinstance(error, (TimeoutError, asyncio.TimeoutError)):
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
        sanitized_message = "Request timed out. Please try a simpler query."
    elif "timeout" in str(error).lower():
        # Additional check for timeout strings (already handled by isinstance above, but keep for safety)
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
        sanitized_message = "Request timed out. Please try a simpler query."
    elif "authentication" in str(error).lower() or "api key" in str(error).lower():
        status_code = status.HTTP_401_UNAUTHORIZED
        sanitized_message = "Authentication error. Please check your API key."
    elif "not found" in str(error).lower():
        status_code = status.HTTP_404_NOT_FOUND
        sanitized_message = "Resource not found."
    elif "validation" in str(error).lower() or "invalid" in str(error).lower():
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        sanitized_message = "Invalid request. Please check your input."

    return HTTPException(
        status_code=status_code,
        detail=sanitized_message,
        headers={"X-Error-ID": error_id},
    )

