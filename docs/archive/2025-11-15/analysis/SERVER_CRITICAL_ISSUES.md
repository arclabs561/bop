# Server Critical Issues Found

## 🔴 CRITICAL FLAWS

### 1. **No Request Isolation - Shared Agent State**
- **Issue**: Global `agent` instance shared across all requests
- **Impact**: CRITICAL - Race conditions, conversation history bleeding between users
- **Evidence**: `agent.conversation_history`, `agent.prior_beliefs`, `agent.recent_queries` are instance variables
- **Fix**: Create per-request agent context or use request-scoped state

### 2. **Mutable Global Orchestrator State**
- **Issue**: `orchestrator.use_constraints` modified per-request (line 172)
- **Impact**: HIGH - Requests interfere with each other
- **Fix**: Don't modify global state, pass as parameter

### 3. **No Error Sanitization**
- **Issue**: Line 252: `raise HTTPException(status_code=500, detail=str(e))`
- **Impact**: HIGH - Exposes internal details (stack traces, paths, API keys)
- **Fix**: Sanitize error messages

### 4. **No Rate Limiting**
- **Issue**: No limits on requests per second/IP
- **Impact**: HIGH - Vulnerable to DoS
- **Fix**: Add rate limiting middleware

### 5. **No Timeout Handling**
- **Issue**: No timeouts on LLM calls, MCP calls, or requests
- **Impact**: HIGH - Requests can hang forever
- **Fix**: Add timeouts

### 6. **No Input Validation**
- **Issue**: No limits on message length
- **Impact**: MEDIUM - Memory/DoS risk
- **Fix**: Validate input size

### 7. **API Key Optional by Default**
- **Issue**: If `BOP_API_KEY` not set, all endpoints are public
- **Impact**: MEDIUM - Security risk if deployed
- **Fix**: Require explicit opt-in for no-auth

### 8. **No Graceful Shutdown**
- **Issue**: No cleanup on shutdown
- **Impact**: MEDIUM - State lost, in-flight requests killed
- **Fix**: Add graceful shutdown

### 9. **CORS Allows All Origins**
- **Issue**: `allow_origins=["*"]` even in private network
- **Impact**: LOW - Risk if network compromised
- **Fix**: Restrict to known origins

### 10. **No Request ID Tracking**
- **Issue**: Can't correlate logs
- **Impact**: LOW - Debugging difficulty
- **Fix**: Add request ID middleware

## ⚠️ OVER-COMPLICATIONS

1. **Static path fallback logic** - Multiple path checks, could serve wrong files
2. **Temporal evolution building** - Complex logic in endpoint, should be in agent
3. **Metrics endpoint error swallowing** - Hides errors silently

## 🟡 MISSING FEATURES

1. **No metrics collection** - Can't monitor performance
2. **No health checks** - Health endpoint doesn't actually check health
3. **No request logging** - Can't audit requests
4. **No connection pooling** - Wastes resources
5. **No cache headers** - Static files re-fetched every time

