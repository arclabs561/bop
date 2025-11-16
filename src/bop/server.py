"""
HTTP server for BOP with constraint solver support.

Accessible via Fly.io private network or with API key authentication.
"""

import asyncio
import logging
import os
import uuid
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Header, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field, field_validator

# .env is auto-loaded by src/bop/__init__.py when package is imported

from .agent import KnowledgeAgent
from .orchestrator import StructuredOrchestrator
from .research import ResearchAgent
from .constraints import PYSAT_AVAILABLE
from .web_ui import router as web_ui_router
from .server_context import get_request_agent, get_request_id, set_request_id
from .middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware, EnhancedRateLimitMiddleware
from .request_limits import RequestSizeLimitMiddleware
from .error_handling import handle_exception, sanitize_error_message, get_request_id
from .input_validation import validate_category, sanitize_string, sanitize_json_input
from .exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# Global agent instance (shared resources)
agent: Optional[KnowledgeAgent] = None
orchestrator: Optional[StructuredOrchestrator] = None

# Rate limiting configuration
RATE_LIMIT_WINDOW = int(os.getenv("BOP_RATE_LIMIT_WINDOW", "60"))  # 1 minute
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("BOP_RATE_LIMIT_MAX", "30"))  # 30 requests per minute

# API Key authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
REQUIRED_API_KEY = os.getenv("BOP_API_KEY", "")
ALLOW_NO_AUTH = os.getenv("BOP_ALLOW_NO_AUTH", "false").lower() == "true"


async def verify_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)):
    """Verify API key for protected endpoints."""
    # If no API key is set and no-auth is explicitly allowed, allow access
    if not REQUIRED_API_KEY and ALLOW_NO_AUTH:
        logger.warning("API key not required - no-auth mode enabled (development only)")
        return True
    
    # If API key is set, require it
    if REQUIRED_API_KEY:
        if not api_key or api_key != REQUIRED_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key. Provide X-API-Key header."
            )
        return True
    
    # Default: require API key unless explicitly allowed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="API key required. Set BOP_API_KEY or BOP_ALLOW_NO_AUTH=true for development."
    )


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID to all requests for tracing."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        set_request_id(request_id)
        # Store in request state for logging middleware
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    global agent, orchestrator
    
    # Initialize agent with constraint solver if enabled
    use_constraints = os.getenv("BOP_USE_CONSTRAINTS", "true").lower() == "true"
    logger.info(f"Initializing BOP server (constraints: {use_constraints})")
    
    try:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        # Enable constraint solver on orchestrator
        if use_constraints and PYSAT_AVAILABLE:
            agent.orchestrator.use_constraints = True
            logger.info("Constraint solver enabled")
        else:
            logger.warning("Constraint solver not available or disabled")
        
        orchestrator = agent.orchestrator
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}", exc_info=True)
        # Don't start server if agent initialization fails
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down BOP server")
    
    # Save knowledge tracker state
    if agent and agent.knowledge_tracker:
        try:
            agent.knowledge_tracker.save()
            logger.info("Saved knowledge tracker state")
        except Exception as e:
            logger.warning(f"Failed to save knowledge tracker state: {e}")
    
    # Rate limit cleanup is handled by middleware


app = FastAPI(
    title="BOP Knowledge Structure Research Agent",
    description="HTTP API for knowledge structure research (Private)",
    version="0.1.0",  # Version in OpenAPI spec is acceptable
    lifespan=lifespan,
    docs_url=None,  # Disable automatic docs (private deployment)
    redoc_url=None,  # Disable ReDoc (private deployment)
    openapi_url=None,  # Disable OpenAPI schema (private deployment)
)

# Add middleware (order matters - first added is outermost, last is innermost)
# Middleware executes in reverse order (last added executes first)
# 1. CORS (outermost - handles preflight requests first)
#    (Added later after CORS config)
# 2. Request size limits (protect against DoS from large requests)
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_body_size=int(os.getenv("BOP_MAX_BODY_SIZE", str(10 * 1024 * 1024))),  # 10MB default
    max_header_size=int(os.getenv("BOP_MAX_HEADER_SIZE", str(8 * 1024))),  # 8KB default
    max_query_string_size=int(os.getenv("BOP_MAX_QUERY_SIZE", str(2 * 1024))),  # 2KB default
)
# 3. Rate limiting (protect against DoS from many requests)
app.add_middleware(
    EnhancedRateLimitMiddleware,
    window_seconds=RATE_LIMIT_WINDOW,
    max_requests=RATE_LIMIT_MAX_REQUESTS,
)
# 4. Request logging (log all requests for audit trail)
app.add_middleware(
    RequestLoggingMiddleware,
    log_body=os.getenv("BOP_LOG_REQUEST_BODY", "false").lower() == "true",
    log_headers=os.getenv("BOP_LOG_REQUEST_HEADERS", "false").lower() == "true",
)
# 5. Security headers (add headers to all responses)
app.add_middleware(SecurityHeadersMiddleware)
# 6. Request ID (innermost - sets ID for all other middleware)
app.add_middleware(RequestIDMiddleware)

# Mount static files and web UI
# Static files path - check both project root and current directory
static_paths = [
    Path(__file__).parent.parent.parent / "static",
    Path("static"),
]
static_path = next((p for p in static_paths if p.exists()), None)
if static_path:
    # Add cache headers for static files
    static_files = StaticFiles(directory=str(static_path))
    app.mount("/static", static_files, name="static")

app.include_router(web_ui_router)

# Add global exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# CORS middleware - restrict to private network
# Default: no CORS (private network doesn't need it)
# Set BOP_CORS_ORIGINS to enable CORS for specific origins
cors_origins_env = os.getenv("BOP_CORS_ORIGINS", "")
if cors_origins_env:
    allowed_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
    # Never allow wildcard in production
    if "*" in allowed_origins and os.getenv("BOP_ALLOW_NO_AUTH", "false").lower() != "true":
        logger.warning("CORS wildcard (*) is not allowed in production. Restricting to empty list.")
        allowed_origins = []
else:
    allowed_origins = []

# CORS middleware (outermost - handles preflight requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True if allowed_origins else False,  # Only allow credentials if origins specified
    allow_methods=["GET", "POST", "OPTIONS"],  # Restrict methods
    allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],  # Restrict headers
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)  # Limit message size
    schema_name: Optional[str] = None  # Renamed to avoid shadowing BaseModel.schema
    research: bool = False
    use_constraints: Optional[bool] = None  # Override default (but don't modify global state)
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message content."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        # Use input validation utility for comprehensive sanitization
        try:
            return sanitize_string(v, max_length=10000)
        except ValueError as e:
            raise ValueError(f"Invalid message: {str(e)}")


class ChatResponse(BaseModel):
    response: str
    schema_used: Optional[str] = None
    research_conducted: bool = False
    tools_called: int = 0
    constraint_solver_used: bool = False
    quality_score: Optional[float] = None
    topology_metrics: Optional[Dict[str, Any]] = None
    # New fields for enhanced display
    response_tiers: Optional[Dict[str, str]] = None
    prior_beliefs: Optional[List[Dict[str, Any]]] = None
    source_matrix: Optional[Dict[str, Dict]] = None
    token_importance: Optional[Dict[str, Any]] = None
    # Temporal fields
    timestamp: Optional[str] = None  # When response was generated
    source_timestamps: Optional[Dict[str, str]] = None  # When each source was accessed
    temporal_evolution: Optional[List[Dict[str, Any]]] = None  # How understanding changed over time (query-level)
    # Session-level temporal fields
    session_knowledge: Optional[Dict[str, Any]] = None  # Knowledge learned in this session
    cross_session_evolution: Optional[List[Dict[str, Any]]] = None  # How concepts evolved across sessions
    session_concepts: Optional[Dict[str, Any]] = None  # Concepts that appeared in this session
    provenance: Optional[Dict[str, Any]] = None
    query_refinement_suggestions: Optional[List[Dict[str, Any]]] = None
    pipeline_uncertainty: Optional[Dict[str, float]] = None  # NEW: Pipeline uncertainty tracking


@app.get("/")
async def root():
    """Health check and info endpoint (public)."""
    # Minimal information disclosure - don't expose internal details
    return {
        "service": "BOP Knowledge Structure Research Agent",
        "status": "running",
        "access": "private",
    }


@app.get("/health")
async def health():
    """Health check endpoint (public) - actually checks system health."""
    # Minimal information disclosure - don't expose internal implementation details
    health_status = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check agent
    if agent:
        health_status["checks"]["agent"] = "ok"
    else:
        health_status["checks"]["agent"] = "not_initialized"
        health_status["status"] = "degraded"
    
    # Check LLM service
    if agent and agent.llm_service:
        try:
            # Quick check - just verify it's initialized
            health_status["checks"]["llm_service"] = "ok"
        except Exception:
            health_status["checks"]["llm_service"] = "error"
            health_status["status"] = "degraded"
    else:
        health_status["checks"]["llm_service"] = "not_available"
        health_status["status"] = "degraded"
    
    # Check orchestrator
    if orchestrator:
        health_status["checks"]["orchestrator"] = "ok"
    else:
        health_status["checks"]["orchestrator"] = "not_initialized"
        health_status["status"] = "degraded"
    
    return health_status


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
async def chat(request: ChatRequest):
    """Chat endpoint with constraint solver support (protected)."""
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    # Get request-scoped agent (isolates conversation state)
    request_agent = get_request_agent(agent)
    request_id = get_request_id()
    
    # Handle constraint solver override (don't modify global state)
    original_use_constraints = None
    if request.use_constraints is not None and orchestrator:
        original_use_constraints = orchestrator.use_constraints
        orchestrator.use_constraints = request.use_constraints and PYSAT_AVAILABLE
    
    try:
        # Add timeout protection
        response = await asyncio.wait_for(
            request_agent.chat(
                message=request.message,
                use_schema=request.schema_name,
                use_research=request.research,
            ),
            timeout=300.0  # 5 minute timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"Request {request_id} timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timed out. Please try a simpler query."
        )
    except Exception as e:
        # Use enhanced error handling
        raise handle_exception(e, request_id=request_id)
    finally:
        # Restore original constraint solver setting
        if original_use_constraints is not None and orchestrator:
            orchestrator.use_constraints = original_use_constraints
    
    # Extract metrics
    tools_called = 0
    topology_metrics = None
    source_timestamps = {}
    temporal_evolution = []
    
    if response.get("research"):
        research_data = response["research"]
        tools_called = research_data.get("tools_called", 0)
        topology_metrics = research_data.get("topology", {})
        
        # Extract source timestamps from research results
        subsolutions = research_data.get("subsolutions", [])
        for subsolution in subsolutions:
            if isinstance(subsolution, dict):
                results = subsolution.get("results", [])
                for result in results:
                    source = result.get("tool", "unknown")
                    # Try to extract timestamp from result metadata
                    if "timestamp" in result:
                        source_timestamps[source] = result["timestamp"]
                    elif "accessed_at" in result:
                        source_timestamps[source] = result["accessed_at"]
        
        # Build temporal evolution from source matrix if available
        source_matrix = response.get("research", {}).get("source_matrix")
        if source_matrix:
            # Group claims by time if temporal data available
            # For now, we'll create a simple evolution based on source diversity
            for claim, data in list(source_matrix.items())[:5]:
                sources = data.get("sources", {})
                if sources:
                    temporal_evolution.append({
                        "claim": claim[:60] + ("..." if len(claim) > 60 else ""),
                        "full_claim": claim,
                        "source_count": len(sources),
                        "consensus": data.get("consensus"),
                        "conflict": data.get("conflict", False),
                    })
    
    # Get current timestamp
    from datetime import datetime, timezone
    current_timestamp = datetime.now(timezone.utc).isoformat()
    
    return ChatResponse(
        response=response.get("response", ""),
        schema_used=response.get("schema_used"),
        research_conducted=response.get("research_conducted", False),
        tools_called=tools_called,
        constraint_solver_used=orchestrator.use_constraints if orchestrator else False,
        quality_score=response.get("quality", {}).get("score") if response.get("quality") else None,
        topology_metrics=topology_metrics,
        response_tiers=response.get("response_tiers"),
        prior_beliefs=response.get("prior_beliefs"),
        source_matrix=response.get("research", {}).get("source_matrix") if response.get("research") else None,
        token_importance=response.get("research", {}).get("token_importance") if response.get("research") else None,
        timestamp=current_timestamp,
        source_timestamps=source_timestamps if source_timestamps else None,
        temporal_evolution=temporal_evolution if temporal_evolution else None,
        session_knowledge=response.get("session_knowledge"),
        cross_session_evolution=response.get("cross_session_evolution"),
        session_concepts=response.get("session_concepts"),
        provenance=response.get("research", {}).get("provenance") if response.get("research") else None,
        query_refinement_suggestions=(
            response.get("query_refinement_suggestions")
            if response.get("query_refinement_suggestions")
            else None
        ),
        pipeline_uncertainty=(
            response.get("research", {}).get("pipeline_uncertainty")
            if response.get("research")
            else None
        ),
    )


@app.get("/constraints/status", dependencies=[Depends(verify_api_key)])
async def constraints_status():
    """Get constraint solver status and metrics (protected)."""
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        )
    
    # Don't expose internal implementation details
    return {
        "enabled": orchestrator.use_constraints,
        "status": "available" if orchestrator.use_constraints else "disabled",
    }


@app.post("/constraints/toggle", dependencies=[Depends(verify_api_key)])
async def toggle_constraints(enabled: bool):
    """Toggle constraint solver on/off (protected)."""
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        )
    
    if enabled and not PYSAT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Constraint solver not available"
        )
    
    orchestrator.use_constraints = enabled
    if enabled and PYSAT_AVAILABLE:
        from .constraints import ConstraintSolver
        orchestrator.constraint_solver = ConstraintSolver()
    
    return {"enabled": orchestrator.use_constraints}


@app.get("/metrics", dependencies=[Depends(verify_api_key)])
async def metrics():
    """Get system metrics and performance data (protected)."""
    if not agent or not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    # Minimize information disclosure - only expose essential metrics
    metrics_data = {
        "status": "operational",
        "topology": {
            "nodes": len(orchestrator.topology.nodes) if orchestrator else 0,
            "edges": len(orchestrator.topology.edges) if orchestrator else 0,
        },
    }
    
    # Add quality feedback metrics if available
    if agent.quality_feedback:
        try:
            summary = agent.quality_feedback.get_performance_summary()
            metrics_data["quality"] = {
                "total_evaluations": summary.get("total_evaluations", 0),
                "avg_score": summary.get("avg_score", 0.0),
            }
        except Exception as e:
            # Log error instead of silently passing
            logger.warning(f"Failed to get quality metrics: {e}")
            metrics_data["quality"] = {"error": "unavailable"}
    
    # Add cache statistics
    try:
        from .cache import get_cache
        cache = get_cache()
        cache_stats = cache.get_stats()
        metrics_data["cache"] = cache_stats
    except Exception as e:
        logger.debug(f"Failed to get cache stats: {e}")
        metrics_data["cache"] = {"error": "unavailable"}
    
    return metrics_data


@app.get("/cache/stats", dependencies=[Depends(verify_api_key)])
async def cache_stats():
    """Get cache statistics (protected)."""
    try:
        from .cache import get_cache
        cache = get_cache()
        return cache.get_stats()
    except Exception as e:
        # Sanitize error message
        logger.error(f"Cache not available: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache service temporarily unavailable"
        )


@app.post("/cache/clear", dependencies=[Depends(verify_api_key)])
async def clear_cache(category: Optional[str] = None):
    """Clear cache (protected)."""
    try:
        from .cache import get_cache
        cache = get_cache()
        
        # Validate category if provided
        if category:
            try:
                category = validate_category(category)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            cache.clear_category(category)
            return {"message": f"Cleared cache category: {category}"}
        else:
            # Clear all categories
            for cat in ["tools", "llm", "tokens", "sessions"]:
                cache.clear_category(cat)
            return {"message": "Cleared all cache categories"}
    except HTTPException:
        raise
    except Exception as e:
        # Use enhanced error handling
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        raise handle_exception(e)


class EvaluateCompareRequest(BaseModel):
    """Request model for evaluate/compare endpoint."""
    query: str = Field(..., min_length=1, max_length=1000)
    iterations: int = Field(default=3, ge=1, le=10)  # Limit iterations
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query content."""
        try:
            return sanitize_string(v, max_length=1000)
        except ValueError as e:
            raise ValueError(f"Invalid query: {str(e)}")


@app.post("/evaluate/compare", dependencies=[Depends(verify_api_key)])
async def evaluate_compare(
    request: EvaluateCompareRequest,
):
    """
    Compare constraint-based vs heuristic tool selection (protected).
    
    Runs the same query multiple times with both approaches
    and returns comparison metrics.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized"
        )
    
    research_agent = ResearchAgent()
    
    results = {
        "query": request.query,
        "iterations": request.iterations,
        "constraints": {"tools_called": [], "costs": [], "info_gains": []},
        "heuristics": {"tools_called": [], "costs": [], "info_gains": []},
    }
    
    from .constraints import create_default_constraints
    constraints = create_default_constraints()
    
    for i in range(request.iterations):
        # With constraints
        orchestrator.use_constraints = True
        if PYSAT_AVAILABLE and not orchestrator.constraint_solver:
            from .constraints import ConstraintSolver
            orchestrator.constraint_solver = ConstraintSolver()
        
        result_constraints = await orchestrator.research_with_schema(
            request.query,
            schema_name="decompose_and_synthesize",
            max_tools_per_subproblem=2,
        )
        
        # Calculate metrics
        tools_constraints = set()
        for subsolution in result_constraints.get("subsolutions", []):
            tools_constraints.update(subsolution.get("tools_used", []))
        
        cost_constraints = sum(
            c.cost for c in constraints if c.tool.value in tools_constraints
        )
        info_constraints = sum(
            c.information_gain for c in constraints if c.tool.value in tools_constraints
        )
        
        results["constraints"]["tools_called"].append(list(tools_constraints))
        results["constraints"]["costs"].append(cost_constraints)
        results["constraints"]["info_gains"].append(info_constraints)
        
        # With heuristics
        orchestrator.use_constraints = False
        result_heuristics = await orchestrator.research_with_schema(
            request.query,
            schema_name="decompose_and_synthesize",
            max_tools_per_subproblem=2,
        )
        
        tools_heuristics = set()
        for subsolution in result_heuristics.get("subsolutions", []):
            tools_heuristics.update(subsolution.get("tools_used", []))
        
        cost_heuristics = sum(
            c.cost for c in constraints if c.tool.value in tools_heuristics
        )
        info_heuristics = sum(
            c.information_gain for c in constraints if c.tool.value in tools_heuristics
        )
        
        results["heuristics"]["tools_called"].append(list(tools_heuristics))
        results["heuristics"]["costs"].append(cost_heuristics)
        results["heuristics"]["info_gains"].append(info_heuristics)
    
    # Calculate averages
    results["constraints"]["avg_cost"] = sum(results["constraints"]["costs"]) / request.iterations
    results["constraints"]["avg_info"] = sum(results["constraints"]["info_gains"]) / request.iterations
    results["heuristics"]["avg_cost"] = sum(results["heuristics"]["costs"]) / request.iterations
    results["heuristics"]["avg_info"] = sum(results["heuristics"]["info_gains"]) / request.iterations
    
    return results


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Fly.io uses PORT, fallback to BOP_PORT or default)
    port = int(os.getenv("PORT", os.getenv("BOP_PORT", "8000")))
    host = os.getenv("BOP_HOST", "0.0.0.0")  # Listen on all interfaces
    
    logger.info(f"Starting BOP server on {host}:{port}")
    logger.info(f"Constraint solver available: {PYSAT_AVAILABLE}")
    logger.info(f"API key required: {bool(REQUIRED_API_KEY)}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")
