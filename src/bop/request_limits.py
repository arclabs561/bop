"""Request size limits and DoS protection middleware."""

import logging
from typing import Callable
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive

logger = logging.getLogger(__name__)

# Default limits
MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB
MAX_HEADER_SIZE = 8 * 1024  # 8KB
MAX_QUERY_STRING_SIZE = 2 * 1024  # 2KB


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request sizes and prevent DoS attacks."""
    
    def __init__(
        self,
        app: ASGIApp,
        max_body_size: int = MAX_BODY_SIZE,
        max_header_size: int = MAX_HEADER_SIZE,
        max_query_string_size: int = MAX_QUERY_STRING_SIZE,
    ):
        super().__init__(app)
        self.max_body_size = max_body_size
        self.max_header_size = max_header_size
        self.max_query_string_size = max_query_string_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        # Check query string size
        query_string = str(request.url.query)
        if len(query_string.encode()) > self.max_query_string_size:
            logger.warning(
                f"Query string too large: {len(query_string)} bytes "
                f"(max: {self.max_query_string_size}) from {request.client.host if request.client else 'unknown'}"
            )
            return JSONResponse(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                content={
                    "error": {
                        "message": "Query string too large",
                        "max_size": self.max_query_string_size,
                    }
                },
            )
        
        # Check header size
        total_header_size = sum(
            len(key.encode()) + len(value.encode())
            for key, value in request.headers.items()
        )
        if total_header_size > self.max_header_size:
            logger.warning(
                f"Headers too large: {total_header_size} bytes "
                f"(max: {self.max_header_size}) from {request.client.host if request.client else 'unknown'}"
            )
            return JSONResponse(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                content={
                    "error": {
                        "message": "Request headers too large",
                        "max_size": self.max_header_size,
                    }
                },
            )
        
        # Check body size (for POST, PUT, PATCH)
        # Note: FastAPI/Starlette reads the body automatically, so we check Content-Length header
        # For actual body reading, we'd need to intercept at a lower level
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    body_size = int(content_length)
                    if body_size > self.max_body_size:
                        logger.warning(
                            f"Request body too large: {body_size} bytes "
                            f"(max: {self.max_body_size}) from {request.client.host if request.client else 'unknown'}"
                        )
                        return JSONResponse(
                            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            content={
                                "error": {
                                    "message": "Request body too large",
                                    "max_size": self.max_body_size,
                                }
                            },
                        )
                except ValueError:
                    # Invalid content-length, let it through (will be caught by FastAPI)
                    pass
        
        return await call_next(request)

