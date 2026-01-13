"""Critical tests for HTTP server - finding flaws."""



def test_global_agent_singleton():
    """CRITICAL: Global agent is a singleton - shared state across requests."""
    # This means concurrent requests share the same agent
    # Could cause race conditions in agent state

    # Agent has instance variables like:
    # - conversation_history
    # - prior_beliefs
    # - recent_queries
    # - knowledge_tracker

    # If two requests come in simultaneously, they'll modify the same state
    # This is a race condition waiting to happen


def test_no_request_isolation():
    """CRITICAL: No request isolation - conversation history shared."""
    # Each request adds to the same conversation_history
    # Request 1: "What is X?"
    # Request 2: "What is Y?"
    # Both see each other's messages in context

    # This is a bug - each request should have isolated context


def test_api_key_optional_by_default():
    """CRITICAL: API key is optional by default - security issue."""
    # If BOP_API_KEY is not set, anyone can access protected endpoints
    # This is fine for development but dangerous if deployed publicly

    # Should require explicit opt-in for no-auth mode


def test_error_exposes_internal_details():
    """CRITICAL: Errors expose internal details to clients."""
    # Line 252: raise HTTPException(status_code=500, detail=str(e))
    # This exposes full exception messages which may contain:
    # - Stack traces
    # - Internal paths
    # - API keys (if in error messages)
    # - Database connection strings

    # Should sanitize error messages


def test_no_rate_limiting():
    """CRITICAL: No rate limiting - vulnerable to DoS."""
    # Anyone can spam requests
    # Each request:
    # - Creates agent if needed
    # - Makes LLM calls
    # - Makes MCP tool calls
    # - Processes research
    #
    # No limits on:
    # - Requests per second
    # - Requests per IP
    # - Concurrent requests
    # - Request size


def test_no_timeout_handling():
    """CRITICAL: No timeout on chat endpoint."""
    # If LLM call hangs, request hangs forever
    # If MCP tool call hangs, request hangs forever
    # No timeout protection

    # Should have:
    # - Request timeout
    # - LLM call timeout
    # - MCP tool call timeout


def test_orchestrator_mutable_state():
    """CRITICAL: Orchestrator state is mutable and shared."""
    # Line 171-172: orchestrator.use_constraints = request.use_constraints
    # This modifies global state
    # Request 1 sets use_constraints=True
    # Request 2 sets use_constraints=False
    # They interfere with each other

    # Should not modify global orchestrator state per-request


def test_no_connection_pooling():
    """CRITICAL: No connection pooling for MCP tools."""
    # Each request creates new connections
    # No reuse of connections
    # Wastes resources


def test_static_files_no_cache_headers():
    """CRITICAL: Static files served without cache headers."""
    # Line 98: StaticFiles(directory=str(static_path))
    # No cache-control headers
    # Browser will re-fetch on every request
    # Wastes bandwidth


def test_cors_allows_all_origins():
    """CRITICAL: CORS allows all origins even in private network."""
    # Line 105: allow_origins=["*"]
    # Comment says "In private network, this is safe"
    # But if network is compromised, this allows any origin

    # Should restrict to known origins even in private network


def test_no_request_id_tracking():
    """CRITICAL: No request ID tracking for debugging."""
    # Can't correlate logs across services
    # Can't trace a request through the system
    # Makes debugging hard


def test_no_metrics_collection():
    """CRITICAL: No metrics collection."""
    # Can't monitor:
    # - Request latency
    # - Error rates
    # - LLM call costs
    # - MCP tool usage
    # - Memory usage
    # - CPU usage

    # Should collect metrics for observability


def test_chat_response_missing_fields():
    """CRITICAL: ChatResponse may have None fields that should be required."""
    # Many Optional fields
    # Client can't tell if field is missing vs. actually None
    # Should use explicit presence indicators


def test_no_input_validation():
    """CRITICAL: No input validation on message length."""
    # Can send arbitrarily long messages
    # Could cause:
    # - Memory issues
    # - LLM token limit issues
    # - DoS attacks


def test_no_output_sanitization():
    """CRITICAL: No sanitization of response content."""
    # Response may contain:
    # - HTML/JavaScript (XSS risk)
    # - SQL injection attempts
    # - Other malicious content

    # Should sanitize before sending to client


def test_lifespan_no_error_handling():
    """CRITICAL: Lifespan has no error handling."""
    # If agent initialization fails, server still starts
    # But agent is None, causing 503 errors
    # Should fail fast or retry


def test_health_endpoint_no_actual_health_check():
    """CRITICAL: Health endpoint doesn't check actual health."""
    # Just returns {"status": "healthy"}
    # Doesn't check:
    # - Agent is initialized
    # - LLM service is available
    # - MCP tools are available
    # - Database/filesystem is accessible

    # Should actually verify system health


def test_metrics_endpoint_no_error_handling():
    """CRITICAL: Metrics endpoint has try/except that swallows errors."""
    # Line 304-312: try/except that passes silently
    # Errors are hidden
    # Should log errors at minimum


def test_evaluate_compare_no_limits():
    """CRITICAL: evaluate/compare has no limits on iterations."""
    # Can request iterations=1000000
    # Will make that many LLM calls
    # Will cost a fortune
    # Will take forever

    # Should limit iterations


def test_no_graceful_shutdown():
    """CRITICAL: No graceful shutdown handling."""
    # On shutdown:
    # - In-flight requests are killed
    # - Agent state is lost
    # - Knowledge tracker not saved
    # - No cleanup

    # Should:
    # - Wait for in-flight requests
    # - Save state
    # - Clean up resources


def test_concurrent_requests_race_condition():
    """CRITICAL: Concurrent requests can cause race conditions."""
    # Multiple requests modifying:
    # - agent.conversation_history
    # - agent.prior_beliefs
    # - agent.recent_queries
    # - orchestrator.use_constraints
    # - knowledge_tracker state

    # Should use locks or request isolation


def test_no_request_body_size_limit():
    """CRITICAL: No limit on request body size."""
    # Can send huge JSON payloads
    # Could cause memory issues
    # DoS attack vector


def test_static_path_fallback_unsafe():
    """CRITICAL: Static path fallback may serve wrong files."""
    # Line 92-96: Checks multiple paths
    # If wrong path exists, serves wrong files
    # Could serve sensitive files if path is wrong


def test_api_key_in_logs():
    """CRITICAL: API key may be logged."""
    # If API key is in error messages, it's logged
    # Should never log API keys


def test_no_csrf_protection():
    """CRITICAL: No CSRF protection."""
    # POST endpoints vulnerable to CSRF
    # Should have CSRF tokens


def test_no_input_sanitization():
    """CRITICAL: No sanitization of user input."""
    # User message is passed directly to agent
    # Could contain:
    # - SQL injection (if agent uses SQL)
    # - Command injection (if agent executes commands)
    # - Prompt injection (definitely possible)

    # Should sanitize or validate input

