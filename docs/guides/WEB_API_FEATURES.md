# BOP Web API Features

## Overview

BOP's FastAPI server now supports:
1. **Session Management** - Create, list, get, and close sessions via API
2. **Adhoc Tools** - Register and call custom HTTP-based tools from the web
3. **MCP Tool Access** - Call MCP tools directly via API (web-accessible)

## Session Management Endpoints

### Create Session
```http
POST /sessions
X-API-Key: your-api-key
Content-Type: application/json

{
  "context": "Research session on information theory",
  "user_id": "user123",
  "metadata": {"topic": "d-separation"}
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "status": "active",
  "context": "Research session on information theory",
  "user_id": "user123",
  "statistics": {
    "evaluation_count": 0,
    "mean_score": 0.0
  }
}
```

### Get Session
```http
GET /sessions/{session_id}
X-API-Key: your-api-key
```

### List Sessions
```http
GET /sessions?user_id=user123&limit=10&session_status=active
X-API-Key: your-api-key
```

**Query Parameters:**
- `group_id` (optional): Filter by group ID
- `user_id` (optional): Filter by user ID
- `limit` (default: 10): Maximum number of sessions to return
- `session_status` (optional): Filter by status (active, closed, archived)

### Close Session
```http
POST /sessions/{session_id}/close
X-API-Key: your-api-key
```

## Adhoc Tool Endpoints

### Register Tool
Register a custom HTTP-based tool that can be called from the web:

```http
POST /tools/register
X-API-Key: your-api-key
Content-Type: application/json

{
  "name": "Weather API",
  "description": "Get weather information for a location",
  "endpoint": "https://api.weather.com/v1/current",
  "method": "GET",
  "headers": {
    "Accept": "application/json"
  },
  "auth": {
    "type": "bearer",
    "token": "your-api-token"
  },
  "params_schema": {
    "type": "object",
    "properties": {
      "location": {"type": "string"},
      "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
    },
    "required": ["location"]
  }
}
```

**Response:**
```json
{
  "tool_id": "adhoc_weather_api",
  "message": "Tool 'Weather API' registered successfully",
  "tool": {
    "name": "Weather API",
    "description": "Get weather information for a location",
    "endpoint": "https://api.weather.com/v1/current",
    "method": "GET",
    "headers": {"Accept": "application/json"},
    "auth": {"type": "bearer", "token": "..."},
    "registered_at": "2025-01-15T10:30:00Z"
  }
}
```

**Authentication Types:**
- `bearer`: `{"type": "bearer", "token": "your-token"}`
- `basic`: `{"type": "basic", "username": "user", "password": "pass"}`

### List Tools
Get all available tools (MCP + adhoc):

```http
GET /tools
X-API-Key: your-api-key
```

**Response:**
```json
{
  "mcp_tools": [
    {
      "name": "mcp_perplexity_deep_research",
      "required": ["query"],
      "optional": ["focus_areas"]
    },
    ...
  ],
  "adhoc_tools": [
    {
      "tool_id": "adhoc_weather_api",
      "name": "Weather API",
      "description": "Get weather information for a location",
      "endpoint": "https://api.weather.com/v1/current",
      "method": "GET"
    },
    ...
  ]
}
```

### Call Tool
Call any tool (MCP or adhoc):

```http
POST /tools/call
X-API-Key: your-api-key
Content-Type: application/json

{
  "tool_name": "adhoc_weather_api",
  "params": {
    "location": "San Francisco",
    "units": "celsius"
  }
}
```

**For MCP tools:**
```json
{
  "tool_name": "mcp_perplexity_search",
  "params": {
    "query": "What is d-separation?",
    "max_results": 5
  }
}
```

**Response:**
```json
{
  "tool": "adhoc_weather_api",
  "result": {
    "temperature": 18,
    "condition": "sunny",
    "location": "San Francisco"
  },
  "status_code": 200,
  "sources": [
    {
      "source": "https://api.weather.com/v1/current",
      "type": "adhoc_tool"
    }
  ],
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Unregister Tool
```http
DELETE /tools/{tool_id}
X-API-Key: your-api-key
```

## Integration with Chat Endpoint

The `/chat` endpoint can use sessions and tools:

```http
POST /chat
X-API-Key: your-api-key
Content-Type: application/json

{
  "message": "What's the weather in San Francisco?",
  "research": true,
  "schema_name": "decompose_and_synthesize"
}
```

The system will:
1. Use registered adhoc tools if they match the query
2. Track the conversation in a session (if session management is enabled)
3. Use MCP tools for research

## Example: Complete Workflow

### 1. Register a Custom Tool
```bash
curl -X POST http://localhost:8000/tools/register \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wikipedia Search",
    "description": "Search Wikipedia articles",
    "endpoint": "https://en.wikipedia.org/api/rest_v1/page/summary",
    "method": "GET"
  }'
```

### 2. Create a Session
```bash
curl -X POST http://localhost:8000/sessions \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Wikipedia research session",
    "user_id": "user123"
  }'
```

### 3. Call the Tool
```bash
curl -X POST http://localhost:8000/tools/call \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "adhoc_wikipedia_search",
    "params": {
      "title": "D-separation"
    }
  }'
```

### 4. Use in Chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain d-separation using Wikipedia",
    "research": true
  }'
```

## Security

All endpoints (except `/health` and `/`) require:
- `X-API-Key` header with valid API key
- Or `BOP_ALLOW_NO_AUTH=true` for development

## Rate Limiting

- Default: 30 requests per minute per IP
- Configurable via `BOP_RATE_LIMIT_MAX` and `BOP_RATE_LIMIT_WINDOW`

## Error Handling

All endpoints return structured error responses:
```json
{
  "detail": "Error message",
  "error_id": "unique-error-id",
  "error_type": "validation_error"
}
```

## Meta Capabilities

BOP can now analyze itself, generate schemas dynamically, and create meta-tools. See `docs/guides/META_CAPABILITIES.md` for:
- Self-analysis endpoints (`/meta/analyze`)
- Dynamic schema generation (`/meta/schemas/generate`)
- Meta-tools (tools that manage other tools)
- Recursive tool orchestration
- Meta-research (research about research)

## See Also

- `QUICK_START_SERVICE.md` - Service deployment guide
- `docs/guides/CAPABILITIES_EXPLORATION.md` - Full capabilities overview
- `docs/guides/META_CAPABILITIES.md` - Meta capabilities (self-analysis, schema generation, etc.)
- `src/bop/server.py` - Implementation details

