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
from datetime import datetime, timezone
from collections import defaultdict
import httpx

from fastapi import FastAPI, HTTPException, Header, Depends, Request, status, Body
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
        
        if enable_skills:
            logger.info("Skills pattern enabled")
        if enable_reminders:
            logger.info("System reminders enabled")
        
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
    enable_skills: bool = False  # Enable Skills pattern for dynamic context loading
    enable_system_reminders: bool = False  # Enable system reminders to keep agent on track
    
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
    
    # Handle per-request feature flags (skills, reminders)
    # These override global settings for this request only
    original_enable_skills = None
    original_enable_reminders = None
    if hasattr(request_agent, 'enable_skills'):
        original_enable_skills = request_agent.enable_skills
        original_enable_reminders = request_agent.enable_system_reminders
        # Override with request-specific settings
        request_agent.enable_skills = request.enable_skills
        request_agent.enable_system_reminders = request.enable_system_reminders
        # Update skills_manager if needed
        if request.enable_skills and not request_agent.skills_manager:
            from .skills import SkillsManager
            request_agent.skills_manager = SkillsManager()
    
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
        # Restore original feature flags
        if original_enable_skills is not None and hasattr(request_agent, 'enable_skills'):
            request_agent.enable_skills = original_enable_skills
            request_agent.enable_system_reminders = original_enable_reminders
    
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


# ============================================================================
# Session Management Endpoints
# ============================================================================

class SessionCreateRequest(BaseModel):
    """Request to create a new session."""
    context: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    """Session response model."""
    session_id: str
    created_at: str
    updated_at: str
    status: str
    context: Optional[str] = None
    user_id: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None


@app.post("/sessions", response_model=SessionResponse, dependencies=[Depends(verify_api_key)])
async def create_session(request: SessionCreateRequest):
    """Create a new session (protected)."""
    if not agent or not agent.quality_feedback or not agent.quality_feedback.session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session management not available"
        )
    
    session_manager = agent.quality_feedback.session_manager
    session_id = session_manager.create_session(
        context=request.context,
        user_id=request.user_id,
        metadata=request.metadata or {},
    )
    
    # Get the created session
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created session"
        )
    
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        status=session.status,
        context=session.context,
        user_id=session.user_id,
        statistics=session.get_statistics(),
    )


@app.get("/sessions/{session_id}", response_model=SessionResponse, dependencies=[Depends(verify_api_key)])
async def get_session(session_id: str):
    """Get session by ID (protected)."""
    if not agent or not agent.quality_feedback or not agent.quality_feedback.session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session management not available"
        )
    
    session_manager = agent.quality_feedback.session_manager
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        status=session.status,
        context=session.context,
        user_id=session.user_id,
        statistics=session.get_statistics(),
    )


@app.get("/sessions", dependencies=[Depends(verify_api_key)])
async def list_sessions(
    group_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 10,
    session_status: Optional[str] = None,  # Renamed to avoid conflict with status module
):
    """List sessions (protected)."""
    if not agent or not agent.quality_feedback or not agent.quality_feedback.session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session management not available"
        )
    
    session_manager = agent.quality_feedback.session_manager
    sessions = session_manager.list_sessions(
        group_id=group_id,
        user_id=user_id,
        limit=limit,
    )
    
    # Filter by status if provided
    if session_status:
        sessions = [s for s in sessions if s.status == session_status]
    
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "status": s.status,
                "context": s.context,
                "user_id": s.user_id,
                "statistics": s.get_statistics(),
            }
            for s in sessions
        ],
        "count": len(sessions),
    }


@app.post("/sessions/{session_id}/close", dependencies=[Depends(verify_api_key)])
async def close_session(session_id: str):
    """Close a session (protected)."""
    if not agent or not agent.quality_feedback or not agent.quality_feedback.session_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session management not available"
        )
    
    session_manager = agent.quality_feedback.session_manager
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    session_manager.close_session(session_id, finalize=True)
    
    # Get updated session
    updated_session = session_manager.get_session(session_id)
    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve closed session"
        )
    
    return {"message": f"Session {session_id} closed", "status": updated_session.status}


# ============================================================================
# Adhoc Tool Endpoints
# ============================================================================

# Registry for adhoc tools
adhoc_tools: Dict[str, Dict[str, Any]] = {}


class ToolCallRequest(BaseModel):
    """Request to call a tool."""
    tool_name: str = Field(..., min_length=1, max_length=100)
    params: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('tool_name')
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        return sanitize_string(v, max_length=100)


class ToolRegisterRequest(BaseModel):
    """Request to register a new adhoc tool."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    endpoint: str = Field(..., min_length=1)  # HTTP endpoint URL
    method: str = Field(default="POST", pattern="^(GET|POST|PUT|DELETE)$")
    headers: Optional[Dict[str, str]] = None
    auth: Optional[Dict[str, str]] = None  # {"type": "bearer", "token": "..."} or {"type": "basic", "username": "...", "password": "..."}
    params_schema: Optional[Dict[str, Any]] = None  # JSON schema for parameters
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return sanitize_string(v, max_length=100)
    
    @field_validator('endpoint')
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        # Basic URL validation
        if not v.startswith(("http://", "https://")):
            raise ValueError("Endpoint must be a valid HTTP/HTTPS URL")
        return v


@app.post("/tools/register", dependencies=[Depends(verify_api_key)])
async def register_tool(request: ToolRegisterRequest):
    """Register a new adhoc tool (protected)."""
    # Validate endpoint is reachable (optional check)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Just check if endpoint exists (HEAD request)
            response = await client.head(request.endpoint)
            if response.status_code >= 400:
                logger.warning(f"Tool endpoint {request.endpoint} returned status {response.status_code}")
    except Exception as e:
        logger.warning(f"Could not validate tool endpoint {request.endpoint}: {e}")
        # Don't fail registration, just warn
    
    tool_id = f"adhoc_{request.name.lower().replace(' ', '_')}"
    
    adhoc_tools[tool_id] = {
        "name": request.name,
        "description": request.description,
        "endpoint": request.endpoint,
        "method": request.method,
        "headers": request.headers or {},
        "auth": request.auth,
        "params_schema": request.params_schema,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    
    logger.info(f"Registered adhoc tool: {tool_id} -> {request.endpoint}")
    
    return {
        "tool_id": tool_id,
        "message": f"Tool '{request.name}' registered successfully",
        "tool": adhoc_tools[tool_id],
    }


@app.get("/tools", dependencies=[Depends(verify_api_key)])
async def list_tools():
    """List all available tools (MCP + adhoc) (protected)."""
    tools = {
        "mcp_tools": [],
        "adhoc_tools": [],
    }
    
    # List MCP tools
    try:
        from .mcp_tools import TOOL_PARAM_MAP
        for tool_name, params in TOOL_PARAM_MAP.items():
            tools["mcp_tools"].append({
                "name": tool_name,
                "required": params.get("required", []),
                "optional": params.get("optional", []),
            })
    except ImportError:
        pass
    
    # List adhoc tools
    for tool_id, tool_info in adhoc_tools.items():
        tools["adhoc_tools"].append({
            "tool_id": tool_id,
            "name": tool_info["name"],
            "description": tool_info["description"],
            "endpoint": tool_info["endpoint"],
            "method": tool_info["method"],
        })
    
    return tools


@app.post("/tools/call", dependencies=[Depends(verify_api_key)])
async def call_tool(request: ToolCallRequest):
    """Call a tool (MCP or adhoc) (protected)."""
    # Check if it's an adhoc tool
    if request.tool_name in adhoc_tools:
        tool_info = adhoc_tools[request.tool_name]
        
        # Prepare request
        headers = tool_info.get("headers", {}).copy()
        
        # Add authentication
        auth = tool_info.get("auth")
        if auth:
            auth_type = auth.get("type", "bearer")
            if auth_type == "bearer":
                headers["Authorization"] = f"Bearer {auth.get('token', '')}"
            elif auth_type == "basic":
                import base64
                username = auth.get("username", "")
                password = auth.get("password", "")
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
        
        # Make HTTP request
        method = tool_info.get("method", "POST").upper()
        endpoint = tool_info["endpoint"]
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(endpoint, params=request.params, headers=headers)
                elif method == "POST":
                    response = await client.post(endpoint, json=request.params, headers=headers)
                elif method == "PUT":
                    response = await client.put(endpoint, json=request.params, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(endpoint, params=request.params, headers=headers)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unsupported HTTP method: {method}"
                    )
                
                response.raise_for_status()
                
                return {
                    "tool": request.tool_name,
                    "result": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                    "status_code": response.status_code,
                    "sources": [{"source": endpoint, "type": "adhoc_tool"}],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except httpx.HTTPError as e:
            logger.error(f"Tool call failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Tool endpoint error: {str(e)}"
            )
    
    # Otherwise, try MCP tool
    try:
        from .mcp_tools import call_mcp_tool
        result = await call_mcp_tool(request.tool_name, **request.params)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return {
            "tool": request.tool_name,
            "result": result.get("result", ""),
            "sources": result.get("sources", []),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mcp_call": result.get("needs_mcp_call", False),
        }
    except Exception as e:
        logger.error(f"MCP tool call failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool call failed: {str(e)}"
        )


@app.delete("/tools/{tool_id}", dependencies=[Depends(verify_api_key)])
async def unregister_tool(tool_id: str):
    """Unregister an adhoc tool (protected)."""
    if tool_id not in adhoc_tools:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found"
        )
    
    del adhoc_tools[tool_id]
    logger.info(f"Unregistered adhoc tool: {tool_id}")
    
    return {"message": f"Tool {tool_id} unregistered"}


# ============================================================================
# Meta Capabilities: Self-Analysis, Schema Generation, Meta-Tools
# ============================================================================

class SelfAnalysisRequest(BaseModel):
    """Request for self-analysis."""
    analysis_type: str = Field(default="performance", pattern="^(performance|behavior|architecture|learning)$")
    depth: int = Field(default=1, ge=1, le=3)  # Analysis depth (1=summary, 2=detailed, 3=comprehensive)
    include_metrics: bool = True
    include_recommendations: bool = True


@app.post("/meta/analyze", dependencies=[Depends(verify_api_key)])
async def self_analyze(request: SelfAnalysisRequest):
    """BOP analyzes its own performance and behavior (protected)."""
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    analysis = {
        "analysis_type": request.analysis_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "depth": request.depth,
    }
    
    if request.analysis_type == "performance":
        # Analyze performance metrics
        if agent.quality_feedback:
            summary = agent.quality_feedback.get_performance_summary()
            analysis["performance"] = summary
            
            if request.depth >= 2 and agent.adaptive_manager:
                insights = agent.adaptive_manager.get_performance_insights()
                analysis["adaptive_insights"] = insights
            
            if request.depth >= 3:
                # Deep analysis: schema effectiveness, tool performance, etc.
                analysis["deep_metrics"] = {
                    "schema_effectiveness": summary.get("schema_performance", {}),
                    "quality_trends": summary.get("trend", "unknown"),
                    "common_issues": summary.get("quality_issue_frequency", {}),
                }
    
    elif request.analysis_type == "behavior":
        # Analyze behavior patterns
        if agent.quality_feedback and agent.quality_feedback.session_manager:
            session_manager = agent.quality_feedback.session_manager
            stats = session_manager.get_aggregate_statistics()
            analysis["behavior"] = {
                "session_count": stats.get("session_count", 0),
                "total_evaluations": stats.get("total_evaluations", 0),
                "mean_score": stats.get("mean_score", 0.0),
                "score_range": f"{stats.get('min_score', 0.0):.3f} - {stats.get('max_score', 0.0):.3f}",
            }
            
            if request.depth >= 2:
                # Query patterns, schema usage patterns
                analysis["patterns"] = {
                    "schemas_used": stats.get("schemas_used", []),
                    "quality_issues": stats.get("quality_issues", {}),
                }
    
    elif request.analysis_type == "architecture":
        # Analyze system architecture and components
        analysis["architecture"] = {
            "components": {
                "agent": agent is not None,
                "orchestrator": orchestrator is not None,
                "quality_feedback": agent.quality_feedback is not None if agent else False,
                "adaptive_manager": agent.adaptive_manager is not None if agent else False,
                "constraint_solver": PYSAT_AVAILABLE and (orchestrator.use_constraints if orchestrator else False),
            },
            "tools_registered": len(adhoc_tools),
            "mcp_tools_available": 0,  # Will be populated if mcp_tools available
        }
        
        if request.depth >= 2:
            # Component health, dependencies
            analysis["health"] = {
                "cache_available": True,  # Would check actual cache
                "session_management": agent.quality_feedback.session_manager is not None if agent and agent.quality_feedback else False,
            }
    
    elif request.analysis_type == "learning":
        # Analyze learning and adaptation
        if agent and agent.adaptive_manager:
            insights = agent.adaptive_manager.get_performance_insights()
            analysis["learning"] = {
                "query_type_performance": insights.get("query_type_performance", {}),
                "schema_recommendations": insights.get("schema_recommendations", {}),
                "research_effectiveness": insights.get("research_effectiveness", {}),
                "length_preferences": insights.get("length_preferences", {}),
            }
            
            if request.depth >= 2:
                # Learning trends, adaptation patterns
                analysis["adaptation"] = {
                    "learning_data_path": str(agent.adaptive_manager.learning_data_path),
                    "has_persisted_data": agent.adaptive_manager.learning_data_path.exists(),
                }
    
    if request.include_recommendations:
        recommendations = []
        if request.analysis_type == "performance":
            if analysis.get("performance", {}).get("trend") == "degrading":
                recommendations.append("Performance is degrading. Consider reviewing recent changes.")
            if analysis.get("performance", {}).get("recent_mean_score", 1.0) < 0.7:
                recommendations.append("Quality scores are low. Consider enabling research for complex queries.")
        elif request.analysis_type == "architecture":
            if not analysis["architecture"]["components"]["constraint_solver"]:
                recommendations.append("Constraint solver not enabled. Consider enabling for complex queries.")
        analysis["recommendations"] = recommendations
    
    return analysis


class SchemaGenerateRequest(BaseModel):
    """Request to generate a new reasoning schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    schema_def: Dict[str, Any] = Field(..., description="Schema structure definition")
    examples: Optional[List[Dict[str, Any]]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return sanitize_string(v, max_length=100).lower().replace(' ', '_')


@app.post("/meta/schemas/generate", dependencies=[Depends(verify_api_key)])
async def generate_schema(request: SchemaGenerateRequest):
    """Generate a new reasoning schema dynamically (protected)."""
    from .schemas import ReasoningSchema, SCHEMA_REGISTRY
    
    # Create new schema
    new_schema = ReasoningSchema(
        name=request.name,
        description=request.description,
        schema_def=request.schema_def,
        examples=request.examples or [],
    )
    
    # Register it
    SCHEMA_REGISTRY[request.name] = new_schema
    
    logger.info(f"Generated new schema: {request.name}")
    
    return {
        "schema": {
            "name": new_schema.name,
            "description": new_schema.description,
            "schema_def": new_schema.schema_def,
            "examples": new_schema.examples,
        },
        "message": f"Schema '{request.name}' generated and registered",
        "total_schemas": len(SCHEMA_REGISTRY),
    }


@app.get("/meta/schemas", dependencies=[Depends(verify_api_key)])
async def list_all_schemas():
    """List all schemas including dynamically generated ones (protected)."""
    from .schemas import SCHEMA_REGISTRY
    
    schemas = []
    for name, schema in SCHEMA_REGISTRY.items():
        schemas.append({
            "name": name,
            "description": schema.description,
            "schema_def": schema.schema_def,
            "examples_count": len(schema.examples),
        })
    
    return {
        "schemas": schemas,
        "count": len(schemas),
    }


class MetaToolRequest(BaseModel):
    """Request to create a meta-tool (tool that manages other tools)."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    operation: str = Field(..., pattern="^(register|unregister|list|call)$")
    target_tool: Optional[str] = None  # Tool to operate on
    tool_config: Optional[Dict[str, Any]] = None  # Config for register operation


@app.post("/meta/tools/create", dependencies=[Depends(verify_api_key)])
async def create_meta_tool(request: MetaToolRequest):
    """Create a meta-tool that can manage other tools (protected)."""
    # Meta-tool endpoint that calls /tools/* endpoints
    meta_tool_id = f"meta_{request.name.lower().replace(' ', '_')}"
    
    # Create endpoint URL (self-referential)
    base_url = os.getenv("BOP_BASE_URL", "http://localhost:8000")
    
    endpoint_map = {
        "register": f"{base_url}/tools/register",
        "unregister": f"{base_url}/tools/{request.target_tool or '{tool_id}'}",
        "list": f"{base_url}/tools",
        "call": f"{base_url}/tools/call",
    }
    
    endpoint = endpoint_map.get(request.operation)
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown operation: {request.operation}"
        )
    
    # Register as adhoc tool
    adhoc_tools[meta_tool_id] = {
        "name": request.name,
        "description": request.description,
        "endpoint": endpoint,
        "method": "POST" if request.operation != "list" else "GET",
        "headers": {"X-API-Key": REQUIRED_API_KEY} if REQUIRED_API_KEY else {},
        "auth": None,
        "params_schema": {
            "operation": request.operation,
            "target_tool": request.target_tool,
            "tool_config": request.tool_config,
        },
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "meta_tool": True,
    }
    
    logger.info(f"Created meta-tool: {meta_tool_id} for operation: {request.operation}")
    
    return {
        "meta_tool_id": meta_tool_id,
        "message": f"Meta-tool '{request.name}' created",
        "operation": request.operation,
        "endpoint": endpoint,
    }


class RecursiveToolRequest(BaseModel):
    """Request to call a tool that calls other tools recursively."""
    tool_name: str = Field(..., min_length=1, max_length=100)
    params: Dict[str, Any] = Field(default_factory=dict)
    recursive_depth: int = Field(default=1, ge=1, le=3)  # Max recursion depth
    tools_to_call: Optional[List[str]] = None  # Tools to call within this tool


@app.post("/meta/tools/recursive", dependencies=[Depends(verify_api_key)])
async def recursive_tool_call(request: RecursiveToolRequest):
    """Call a tool that can call other tools recursively (protected)."""
    if request.recursive_depth > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum recursion depth is 3"
        )
    
    results: Dict[str, Any] = {
        "tool": request.tool_name,
        "recursive_depth": request.recursive_depth,
        "results": [],
        "nested_calls": [],
    }
    
    # First, call the main tool
    try:
        main_result = await call_tool(ToolCallRequest(
            tool_name=request.tool_name,
            params=request.params,
        ))
        results["results"].append({
            "depth": 0,
            "tool": request.tool_name,
            "result": main_result,
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Main tool call failed: {str(e)}"
        )
    
    # If recursive_depth > 1 and tools_to_call specified, call those tools
    if request.recursive_depth > 1 and request.tools_to_call:
        for nested_tool in request.tools_to_call:
            try:
                nested_result = await call_tool(ToolCallRequest(
                    tool_name=nested_tool,
                    params=request.params.get("nested_params", {}),
                ))
                results["nested_calls"].append({
                    "depth": 1,
                    "tool": nested_tool,
                    "result": nested_result,
                })
            except Exception as e:
                logger.warning(f"Nested tool call failed: {nested_tool} - {e}")
                results["nested_calls"].append({
                    "depth": 1,
                    "tool": nested_tool,
                    "error": str(e),
                })
    
    results["timestamp"] = datetime.now(timezone.utc).isoformat()
    return results


class MetaResearchRequest(BaseModel):
    """Request for meta-research (research about research)."""
    query: str = Field(..., min_length=1, max_length=1000)
    research_type: str = Field(default="patterns", pattern="^(patterns|effectiveness|optimization)$")
    analyze_own_research: bool = True  # Analyze BOP's own research patterns


@app.post("/meta/research", dependencies=[Depends(verify_api_key)])
async def meta_research(request: MetaResearchRequest):
    """Conduct meta-research: research about research patterns and effectiveness (protected)."""
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    meta_analysis = {
        "query": request.query,
        "research_type": request.research_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    if request.analyze_own_research and agent.quality_feedback:
        # Analyze BOP's own research patterns
        summary = agent.quality_feedback.get_performance_summary()
        if isinstance(summary, dict):
            research_metrics = summary.get("research_effectiveness", {})
            
            meta_analysis["own_research"] = {
                "research_impact": research_metrics if isinstance(research_metrics, dict) else {},
                "tool_usage": summary.get("tool_usage", {}) if isinstance(summary.get("tool_usage"), dict) else {},
                "quality_with_research": summary.get("quality_with_research", 0.0) if isinstance(summary.get("quality_with_research"), (int, float)) else 0.0,
                "quality_without_research": summary.get("quality_without_research", 0.0) if isinstance(summary.get("quality_without_research"), (int, float)) else 0.0,
            }
    
    # Conduct actual research on the meta-query
    try:
        research_result = await agent.chat(
            message=request.query,
            use_research=True,
            use_schema="decompose_and_synthesize",
        )
        
        research_data = research_result.get("research", {}) if isinstance(research_result.get("research"), dict) else {}
        meta_analysis["research_result"] = {
            "response": str(research_result.get("response", ""))[:500],  # Truncate for response
            "tools_called": research_data.get("tools_called", 0) if isinstance(research_data.get("tools_called"), int) else 0,
            "sources_count": len(research_data.get("sources", [])) if isinstance(research_data.get("sources"), list) else 0,
        }
    except Exception as e:
        logger.error(f"Meta-research failed: {e}")
        meta_analysis["research_error"] = str(e)
    
    return meta_analysis


# ============================================================================
# Research-Informed Meta Capabilities (Based on MetaAgent, Bayesian Meta-Learning)
# ============================================================================

# Experience storage for dynamic context engineering
experience_store: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # query_type -> experiences


class ReflectionRequest(BaseModel):
    """Request for self-reflection or verified reflection."""
    query: str = Field(..., min_length=1, max_length=1000)
    response: str = Field(..., min_length=1)
    reasoning_trajectory: Optional[Dict[str, Any]] = None  # Optional: full reasoning path
    tools_used: Optional[List[str]] = None
    reflection_type: str = Field(default="self", pattern="^(self|verified)$")
    ground_truth: Optional[str] = None  # Required for verified reflection
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        return sanitize_string(v, max_length=1000)


@app.post("/meta/reflect", dependencies=[Depends(verify_api_key)])
async def reflect(request: ReflectionRequest):
    """
    Self-reflection and verified reflection (HIGHEST PRIORITY).
    
    Based on MetaAgent research: distills actionable experience from task completion.
    Self-reflection: reviews reasoning without ground truth.
    Verified reflection: compares with ground truth to extract generalizable insights.
    """
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    if request.reflection_type == "verified" and not request.ground_truth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ground_truth required for verified reflection"
        )
    
    # Use LLM to perform reflection
    reflection_prompt = f"""Reflect on this task completion:

Query: {request.query}
Response: {request.response[:500]}...
Tools Used: {', '.join(request.tools_used or [])}

"""
    
    if request.reflection_type == "verified":
        reflection_prompt += f"""Ground Truth: {request.ground_truth}

Analyze:
1. What worked well? (successful strategies, effective tool usage)
2. What didn't work? (errors, ineffective approaches)
3. Generalizable insights: What principles can be extracted?
4. How to improve next time?

Focus on meta-level insights that apply to similar tasks, not just this specific case.
"""
    else:
        reflection_prompt += """Analyze:
1. Review reasoning trajectory for validity and factual grounding
2. Identify any uncertainty or flaws
3. What could be improved?
4. What strategies were effective?

Focus on actionable insights for future tasks.
"""
    
    try:
        # Use agent's LLM service for reflection
        if not agent.llm_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM service not available"
            )
        reflection_text = await agent.llm_service.generate_response(
            message=reflection_prompt,
            context=None,
            schema=None,
        )
        
        # Classify query type for experience storage
        if agent.adaptive_manager:
            query_type = agent.adaptive_manager._classify_query(request.query)
        else:
            query_type = "general"
        
        # Extract structured insights
        insights = {
            "query": request.query,
            "query_type": query_type,
            "reflection_type": request.reflection_type,
            "reflection_text": reflection_text,
            "tools_used": request.tools_used or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # For verified reflection, extract success/failure patterns
        if request.reflection_type == "verified":
            # Simple extraction: look for patterns in reflection
            successes: List[str] = []
            failures: List[str] = []
            improvements: List[str] = []
            
            # Parse reflection text for structured insights (simplified)
            if "worked well" in reflection_text.lower() or "success" in reflection_text.lower():
                # Extract success patterns
                pass
            if "didn't work" in reflection_text.lower() or "error" in reflection_text.lower():
                # Extract failure patterns
                pass
            if "improve" in reflection_text.lower() or "next time" in reflection_text.lower():
                # Extract improvement suggestions
                pass
            
            insights["successes"] = successes
            insights["failures"] = failures
            insights["improvements"] = improvements
        
        # Store experience for dynamic context engineering
        experience_store[query_type].append(insights)
        
        # Limit stored experiences per query type (keep most recent 50)
        if len(experience_store[query_type]) > 50:
            experience_store[query_type] = experience_store[query_type][-50:]
        
        return {
            "reflection": reflection_text,
            "insights": insights,
            "incorporated": True,
            "message": f"Reflection stored for {query_type} queries"
        }
    
    except Exception as e:
        logger.error(f"Reflection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reflection failed: {str(e)}"
        )


class ToolLearningRequest(BaseModel):
    """Request to learn from tool usage."""
    query_type: str = Field(..., min_length=1, max_length=100)
    tools_used: List[str] = Field(..., min_items=1)
    outcome: str = Field(..., pattern="^(success|failure|partial)$")
    quality_score: float = Field(..., ge=0.0, le=1.0)
    query: Optional[str] = None  # Optional: original query for context


@app.post("/meta/tools/learn", dependencies=[Depends(verify_api_key)])
async def learn_tool_usage(request: ToolLearningRequest):
    """
    Tool meta-learning: learn which tools work best for which tasks (HIGH PRIORITY).
    
    Based on MetaAgent research: learning to use tools effectively through experience.
    """
    if not agent or not agent.adaptive_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Adaptive manager not available"
        )
    
    # Update tool performance in adaptive manager
    for tool in request.tools_used:
        agent.adaptive_manager.tool_performance[tool].append(request.quality_score)
    
    # Compute tool effectiveness per query type
    tool_effectiveness: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(list))
    
    # Aggregate tool performance by query type
    if agent.adaptive_manager.tool_performance:
        for tool, scores in agent.adaptive_manager.tool_performance.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                # For now, assign to all query types (could be refined)
                for q_type in ["factual", "procedural", "analytical", "comparative", "evaluative"]:
                    tool_effectiveness[q_type][tool] = avg_score
    
    # Get recommendations
    query_type = request.query_type.lower()
    recommendations: Dict[str, List[str]] = {
        "best_tools": [],
        "avoid": [],
    }
    
    if query_type in tool_effectiveness:
        tools_for_type = tool_effectiveness[query_type]
        sorted_tools = sorted(tools_for_type.items(), key=lambda x: x[1], reverse=True)
        
        # Best tools (top 3)
        recommendations["best_tools"] = [tool for tool, score in sorted_tools[:3] if score > 0.7]
        
        # Tools to avoid (bottom 2)
        recommendations["avoid"] = [tool for tool, score in sorted_tools[-2:] if score < 0.5]
    
    # Save learning
    agent.adaptive_manager._save_learning()
    
    return {
        "tool_effectiveness": dict(tool_effectiveness),
        "recommendations": recommendations,
        "message": f"Learned from {len(request.tools_used)} tools for {request.query_type} queries",
        "total_tool_observations": sum(len(scores) for scores in agent.adaptive_manager.tool_performance.values()),
    }


@app.get("/meta/context/experience", dependencies=[Depends(verify_api_key)])
async def get_experience(query_type: Optional[str] = None, limit: int = 10):
    """
    Get accumulated experience for dynamic context engineering (HIGH PRIORITY).
    
    Based on MetaAgent research: experience is dynamically incorporated into future contexts.
    """
    if query_type:
        experiences = experience_store.get(query_type.lower(), [])[-limit:]
    else:
        # Get experiences from all query types
        all_experiences = []
        for q_type, exps in experience_store.items():
            all_experiences.extend(exps[-limit:])
        # Sort by timestamp, most recent first
        all_experiences.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        experiences = all_experiences[:limit]
    
    # Format experiences for context injection
    formatted_experiences = []
    for exp in experiences:
        formatted_experiences.append({
            "query_type": exp.get("query_type", "general"),
            "insights": exp.get("reflection_text", "")[:200],  # Truncate for context
            "reflection_type": exp.get("reflection_type", "self"),
            "applicable_to": [exp.get("query_type", "general")],
            "confidence": 0.8 if exp.get("reflection_type") == "verified" else 0.6,
            "timestamp": exp.get("timestamp"),
        })
    
    return {
        "experiences": formatted_experiences,
        "total_experiences": sum(len(exps) for exps in experience_store.values()),
        "by_query_type": {q_type: len(exps) for q_type, exps in experience_store.items()},
    }


@app.post("/meta/context/inject", dependencies=[Depends(verify_api_key)])
async def inject_experience(
    request: Dict[str, Any] = Body(..., description="Request with query and optional max_experiences"),
):
    """
    Get experience to inject into context for a query (dynamic context engineering).
    
    Automatically selects relevant experiences based on query type and injects them
    into the context for improved task planning and tool use.
    """
    if not agent or not agent.adaptive_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    # Extract query and max_experiences from request body
    query = request.get("query", "")
    if not query or len(query) < 1 or len(query) > 1000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query must be between 1 and 1000 characters"
        )
    
    max_experiences = request.get("max_experiences", 5)
    if not isinstance(max_experiences, int) or max_experiences < 1 or max_experiences > 20:
        max_experiences = 5
    
    # Classify query
    query_type = agent.adaptive_manager._classify_query(query)
    
    # Get relevant experiences
    relevant_experiences = experience_store.get(query_type, [])
    
    # Also get general experiences
    general_experiences = experience_store.get("general", [])
    
    # Combine and sort by relevance (verified > self, recent > old)
    all_experiences = relevant_experiences + general_experiences
    all_experiences.sort(
        key=lambda x: (
            1 if x.get("reflection_type") == "verified" else 0,
            x.get("timestamp", ""),
        ),
        reverse=True,
    )
    
    # Select top experiences
    selected = all_experiences[:max_experiences]
    
    # Format for context injection
    context_experience = "\n\n## Previous Task Experience:\n"
    for i, exp in enumerate(selected, 1):
        context_experience += f"\n{i}. {exp.get('reflection_text', '')[:300]}...\n"
    
    return {
        "query": query,
        "query_type": query_type,
        "context_experience": context_experience,
        "experiences_used": len(selected),
        "injection_ready": True,
    }


@app.get("/meta/tools/effectiveness", dependencies=[Depends(verify_api_key)])
async def get_tool_effectiveness(query_type: Optional[str] = None):
    """Get tool effectiveness metrics (tool meta-learning)."""
    if not agent or not agent.adaptive_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Adaptive manager not available"
        )
    
    effectiveness: Dict[str, Dict[str, float]] = {}
    
    # Compute effectiveness per tool
    for tool, scores in agent.adaptive_manager.tool_performance.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            count = len(scores)
            
            # Group by query type if we have that data
            # For now, show overall effectiveness
            effectiveness[tool] = {
                "average_score": avg_score,
                "observation_count": count,
                "min_score": min(scores),
                "max_score": max(scores),
            }
    
    # Get recommendations
    recommendations = {}
    if query_type and agent.adaptive_manager:
        strategy = agent.adaptive_manager.get_adaptive_strategy(
            query=f"example {query_type} query"
        )
        recommendations = {
            "recommended_tools": strategy.tool_preferences,
            "confidence": strategy.confidence,
        }
    
    return {
        "tool_effectiveness": effectiveness,
        "recommendations": recommendations,
        "total_tools_tracked": len(effectiveness),
    }


@app.get("/meta/self", dependencies=[Depends(verify_api_key)])
async def meta_self():
    """Get meta-information about BOP itself (protected)."""
    # Get actual counts
    try:
        from .schemas import SCHEMA_REGISTRY
        schema_count = len(SCHEMA_REGISTRY)
    except ImportError:
        schema_count = 0
    
    try:
        from .mcp_tools import TOOL_PARAM_MAP
        mcp_count = len(TOOL_PARAM_MAP)
    except ImportError:
        mcp_count = 0
    
    # Count experiences
    total_experiences = sum(len(exps) for exps in experience_store.values())
    
    return {
        "system": "BOP: Knowledge Structure Research Agent",
        "version": "1.0.0",  # Could be from __version__
        "capabilities": {
            "research": True,
            "schemas": schema_count,
            "tools": {
                "mcp": mcp_count,
                "adhoc": len(adhoc_tools),
                "meta": len([t for t in adhoc_tools.values() if t.get("meta_tool")]),
            },
            "sessions": agent.quality_feedback.session_manager is not None if agent and agent.quality_feedback else False,
            "adaptive_learning": agent.adaptive_manager is not None if agent else False,
            "constraint_solver": PYSAT_AVAILABLE,
            "meta_learning": {
                "experiences_stored": total_experiences,
                "reflection_enabled": True,
                "tool_meta_learning": agent.adaptive_manager is not None if agent else False,
                "dynamic_context": True,
            },
        },
        "meta_endpoints": [
            "/meta/analyze",
            "/meta/schemas/generate",
            "/meta/schemas",
            "/meta/tools/create",
            "/meta/tools/recursive",
            "/meta/research",
            "/meta/reflect",  # NEW: Self-reflection
            "/meta/tools/learn",  # NEW: Tool meta-learning
            "/meta/context/experience",  # NEW: Dynamic context
            "/meta/context/inject",  # NEW: Context injection
            "/meta/tools/effectiveness",  # NEW: Tool effectiveness
            "/meta/self",
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Fly.io uses PORT, fallback to BOP_PORT or default)
    port = int(os.getenv("PORT", os.getenv("BOP_PORT", "8000")))
    host = os.getenv("BOP_HOST", "0.0.0.0")  # Listen on all interfaces
    
    logger.info(f"Starting BOP server on {host}:{port}")
    logger.info(f"Constraint solver available: {PYSAT_AVAILABLE}")
    logger.info(f"API key required: {bool(REQUIRED_API_KEY)}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")
