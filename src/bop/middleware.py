"""Security and observability middleware for BOP server."""

import json
import logging
import time
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Remove server header if present (uvicorn adds it)
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for audit trail and debugging."""
    
    def __init__(self, app: ASGIApp, log_body: bool = False, log_headers: bool = False):
        super().__init__(app)
        self.log_body = log_body
        self.log_headers = log_headers
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get request ID from context (set by RequestIDMiddleware)
        request_id = getattr(request.state, "request_id", None)
        if not request_id:
            # Fallback if RequestIDMiddleware hasn't run
            import uuid
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        
        # Start timer
        start_time = time.time()
        
        # Log request
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "method": method,
            "path": path,
            "query_params": query_params,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "status_code": None,
            "duration_ms": None,
            "error": None,
        }
        
        # Add headers if requested (but sanitize sensitive ones)
        if self.log_headers:
            headers = dict(request.headers)
            # Sanitize sensitive headers
            for key in ["authorization", "x-api-key", "cookie", "set-cookie"]:
                if key.lower() in headers:
                    headers[key.lower()] = "[REDACTED]"
            log_data["headers"] = headers
        
        # Add body if requested (but limit size and sanitize)
        if self.log_body and method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body and len(body) > 1024 * 1024:  # 1MB max
                    log_data["body"] = "[BODY TOO LARGE - TRUNCATED]"
                elif body:
                    body_str = body.decode("utf-8", errors="replace")[:1024]
                    # Try to parse as JSON and sanitize
                    try:
                        body_json = json.loads(body_str)
                        # Sanitize sensitive fields (case-insensitive)
                        if isinstance(body_json, dict):
                            for key in ["api_key", "password", "token", "secret", "x-api-key"]:
                                # Find actual key (case-insensitive)
                                actual_key = next(
                                    (k for k in body_json.keys() if k.lower() == key.lower()),
                                    None
                                )
                                if actual_key:
                                    body_json[actual_key] = "[REDACTED]"
                        log_data["body"] = body_json
                    except json.JSONDecodeError:
                        # Sanitize non-JSON body
                        if any(pattern in body_str.lower() for pattern in ["<script", "javascript:", "onerror="]):
                            log_data["body"] = "[POTENTIALLY DANGEROUS CONTENT - REDACTED]"
                        else:
                            log_data["body"] = body_str[:512]  # Further limit non-JSON
            except Exception as e:
                log_data["body_error"] = "Failed to read body"
        
        # Process request
        error_occurred = False
        try:
            response = await call_next(request)
            log_data["status_code"] = response.status_code
        except Exception as e:
            error_occurred = True
            log_data["status_code"] = 500
            log_data["error"] = str(e)
            logger.error(f"Request error: {log_data}", exc_info=True)
            # Re-raise to let FastAPI handle it
            raise
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            log_data["duration_ms"] = round(duration_ms, 2)
            
            # Log based on status code
            if error_occurred or log_data["status_code"] >= 500:
                logger.error(f"Request: {json.dumps(log_data)}")
            elif log_data["status_code"] >= 400:
                logger.warning(f"Request: {json.dumps(log_data)}")
            else:
                logger.info(f"Request: {json.dumps(log_data)}")
        
        return response


class EnhancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting with headers and better tracking."""
    
    def __init__(self, app: ASGIApp, window_seconds: int = 60, max_requests: int = 30):
        super().__init__(app)
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        # In-memory store (TODO: Replace with Redis for multi-instance)
        self._rate_limit_store: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/"]:
            return await call_next(request)
        
        # Get client identifier (IP or API key if available)
        client_ip = request.client.host if request.client else "unknown"
        
        # Try to get API key for per-key rate limiting
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Use API key as identifier (allows per-key rate limiting)
            identifier = f"api_key:{api_key[:8]}..."  # Truncate for logging
        else:
            identifier = f"ip:{client_ip}"
        
        # Check rate limit
        now = time.time()
        if identifier in self._rate_limit_store:
            # Remove old entries
            self._rate_limit_store[identifier] = [
                t for t in self._rate_limit_store[identifier]
                if now - t < self.window_seconds
            ]
            
            # Check limit
            request_count = len(self._rate_limit_store[identifier])
            if request_count >= self.max_requests:
                # Calculate reset time
                oldest_request = min(self._rate_limit_store[identifier])
                reset_time = int(oldest_request + self.window_seconds)
                
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds.",
                        "limit": self.max_requests,
                        "window_seconds": self.window_seconds,
                        "reset_at": reset_time,
                    }
                )
                
                # Add rate limit headers
                response.headers["X-RateLimit-Limit"] = str(self.max_requests)
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(reset_time)
                
                logger.warning(f"Rate limit exceeded: {identifier} ({request_count} requests)")
                return response
            
            # Add to store
            self._rate_limit_store[identifier].append(now)
            remaining = self.max_requests - len(self._rate_limit_store[identifier])
        else:
            # First request
            self._rate_limit_store[identifier] = [now]
            remaining = self.max_requests - 1
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful requests
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.window_seconds)
        
        return response
    
    def clear_expired(self):
        """Clear expired entries (call periodically)."""
        now = time.time()
        expired_keys = [
            key for key, timestamps in self._rate_limit_store.items()
            if not any(now - t < self.window_seconds for t in timestamps)
        ]
        for key in expired_keys:
            del self._rate_limit_store[key]

