"""Global exception handlers for FastAPI app."""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .error_handling import handle_exception, create_error_response, get_request_id

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions with error IDs."""
    request_id = getattr(request.state, "request_id", None)
    error_id = exc.headers.get("X-Error-ID") if exc.headers else None
    
    # If error ID already set, use it; otherwise create one
    if not error_id:
        import uuid
        error_id = str(uuid.uuid4())
    
    return create_error_response(
        status_code=exc.status_code,
        detail=exc.detail,
        error_id=error_id,
        error_type="http_exception",
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors with sanitized messages."""
    request_id = getattr(request.state, "request_id", None)
    
    # Sanitize validation errors
    errors = exc.errors()
    sanitized_errors = []
    for error in errors:
        # Don't expose internal field names or paths
        sanitized_error = {
            "field": error.get("loc", ["unknown"])[-1] if error.get("loc") else "unknown",
            "message": "Invalid input",
        }
        # Only include safe error details
        if "type" in error:
            sanitized_error["type"] = error["type"]
        sanitized_errors.append(sanitized_error)
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Validation error. Please check your input.",
        error_type="validation_error",
        additional_data={"errors": sanitized_errors},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions with sanitized error messages."""
    request_id = getattr(request.state, "request_id", None)
    
    # Use enhanced error handling
    http_exception = handle_exception(exc, request_id=request_id)
    
    return create_error_response(
        status_code=http_exception.status_code,
        detail=http_exception.detail,
        error_id=http_exception.headers.get("X-Error-ID") if http_exception.headers else None,
        error_type="internal_error",
    )

