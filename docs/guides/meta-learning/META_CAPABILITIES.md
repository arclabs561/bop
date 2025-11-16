# BOP Meta Capabilities

BOP can now analyze itself, generate new reasoning schemas dynamically, create meta-tools, and conduct recursive tool orchestration. This is **meta** - BOP thinking about BOP.

**Note**: See `docs/guides/META_CAPABILITIES_REFINED.md` for research-informed priorities based on latest MetaAgent, Bayesian Meta-Learning, and self-improving AI research.

## Self-Analysis

### Analyze Performance
```http
POST /meta/analyze
X-API-Key: your-api-key
Content-Type: application/json

{
  "analysis_type": "performance",
  "depth": 2,
  "include_recommendations": true
}
```

**Analysis Types:**
- `performance`: Analyze quality scores, schema effectiveness, trends
- `behavior`: Analyze query patterns, session statistics, usage patterns
- `architecture`: Analyze system components, health, dependencies
- `learning`: Analyze adaptive learning, query type performance, recommendations

**Depth Levels:**
- `1`: Summary (basic metrics)
- `2`: Detailed (includes insights, patterns)
- `3`: Comprehensive (deep metrics, trends, full analysis)

**Response:**
```json
{
  "analysis_type": "performance",
  "depth": 2,
  "performance": {
    "total_evaluations": 150,
    "recent_mean_score": 0.82,
    "trend": "improving",
    "schema_performance": {
      "decompose_and_synthesize": 0.85,
      "chain_of_thought": 0.78
    }
  },
  "adaptive_insights": {
    "query_type_performance": {...},
    "schema_recommendations": {...}
  },
  "recommendations": [
    "Performance is improving. Continue current approach.",
    "Consider using decompose_and_synthesize for analytical queries."
  ]
}
```

## Dynamic Schema Generation

### Generate New Schema
```http
POST /meta/schemas/generate
X-API-Key: your-api-key
Content-Type: application/json

{
  "name": "causal_analysis",
  "description": "Analyze causal relationships and dependencies",
  "schema_def": {
    "causes": "Identify root causes",
    "effects": "Identify effects and outcomes",
    "mechanisms": "Explain causal mechanisms",
    "evidence": "Evidence supporting causal claims"
  },
  "examples": [
    {
      "input": "Why does X cause Y?",
      "hydrated": {
        "causes": "X introduces mechanism Z",
        "effects": "Y occurs as result of Z",
        "mechanisms": "Z triggers pathway...",
        "evidence": "Studies show..."
      }
    }
  ]
}
```

**Response:**
```json
{
  "schema": {
    "name": "causal_analysis",
    "description": "Analyze causal relationships and dependencies",
    "schema_def": {...},
    "examples": [...]
  },
  "message": "Schema 'causal_analysis' generated and registered",
  "total_schemas": 6
}
```

### List All Schemas
```http
GET /meta/schemas
X-API-Key: your-api-key
```

Returns all schemas including dynamically generated ones.

## Meta-Tools

### Create Meta-Tool
Create a tool that manages other tools:

```http
POST /meta/tools/create
X-API-Key: your-api-key
Content-Type: application/json

{
  "name": "Tool Manager",
  "description": "Manages tool registration and calls",
  "operation": "register",
  "tool_config": {
    "name": "Weather API",
    "endpoint": "https://api.weather.com/v1/current"
  }
}
```

**Operations:**
- `register`: Register a new tool
- `unregister`: Unregister a tool
- `list`: List all tools
- `call`: Call a tool

**Response:**
```json
{
  "meta_tool_id": "meta_tool_manager",
  "message": "Meta-tool 'Tool Manager' created",
  "operation": "register",
  "endpoint": "http://localhost:8000/tools/register"
}
```

## Recursive Tool Orchestration

### Call Tools Recursively
Call a tool that calls other tools:

```http
POST /meta/tools/recursive
X-API-Key: your-api-key
Content-Type: application/json

{
  "tool_name": "adhoc_research_pipeline",
  "params": {
    "query": "What is d-separation?",
    "nested_params": {
      "max_results": 5
    }
  },
  "recursive_depth": 2,
  "tools_to_call": [
    "mcp_perplexity_search",
    "mcp_firecrawl_search"
  ]
}
```

**Response:**
```json
{
  "tool": "adhoc_research_pipeline",
  "recursive_depth": 2,
  "results": [
    {
      "depth": 0,
      "tool": "adhoc_research_pipeline",
      "result": {...}
    }
  ],
  "nested_calls": [
    {
      "depth": 1,
      "tool": "mcp_perplexity_search",
      "result": {...}
    },
    {
      "depth": 1,
      "tool": "mcp_firecrawl_search",
      "result": {...}
    }
  ]
}
```

**Max Recursion Depth:** 3 (prevents infinite loops)

## Meta-Research

### Research About Research
Conduct research while analyzing your own research patterns:

```http
POST /meta/research
X-API-Key: your-api-key
Content-Type: application/json

{
  "query": "What are effective research strategies for knowledge systems?",
  "research_type": "effectiveness",
  "analyze_own_research": true
}
```

**Research Types:**
- `patterns`: Analyze research patterns
- `effectiveness`: Analyze research effectiveness
- `optimization`: Optimize research strategies

**Response:**
```json
{
  "query": "What are effective research strategies...",
  "research_type": "effectiveness",
  "own_research": {
    "research_impact": {
      "analytical": {"improvement": 0.15},
      "factual": {"improvement": 0.02}
    },
    "quality_with_research": 0.85,
    "quality_without_research": 0.72
  },
  "research_result": {
    "response": "Effective research strategies include...",
    "tools_called": 3,
    "sources_count": 8
  }
}
```

## Self-Information

### Get Meta-Information
```http
GET /meta/self
X-API-Key: your-api-key
```

**Response:**
```json
{
  "system": "BOP: Knowledge Structure Research Agent",
  "version": "1.0.0",
  "capabilities": {
    "research": true,
    "schemas": 6,
    "tools": {
      "mcp": 8,
      "adhoc": 3,
      "meta": 1
    },
    "sessions": true,
    "adaptive_learning": true,
    "constraint_solver": true
  },
  "meta_endpoints": [
    "/meta/analyze",
    "/meta/schemas/generate",
    "/meta/schemas",
    "/meta/tools/create",
    "/meta/tools/recursive",
    "/meta/research",
    "/meta/self"
  ]
}
```

## Example: Complete Meta Workflow

### 1. Analyze Yourself
```bash
curl -X POST http://localhost:8000/meta/analyze \
  -H "X-API-Key: your-key" \
  -d '{
    "analysis_type": "performance",
    "depth": 3
  }'
```

### 2. Generate Custom Schema
```bash
curl -X POST http://localhost:8000/meta/schemas/generate \
  -H "X-API-Key: your-key" \
  -d '{
    "name": "meta_analysis",
    "description": "Analyze systems and their behavior",
    "schema_def": {
      "system": "System to analyze",
      "metrics": "Metrics to collect",
      "insights": "Insights derived",
      "recommendations": "Recommendations for improvement"
    }
  }'
```

### 3. Create Meta-Tool
```bash
curl -X POST http://localhost:8000/meta/tools/create \
  -H "X-API-Key: your-key" \
  -d '{
    "name": "Self-Improvement Tool",
    "description": "Tool that improves itself",
    "operation": "call"
  }'
```

### 4. Use Meta-Tool Recursively
```bash
curl -X POST http://localhost:8000/meta/tools/recursive \
  -H "X-API-Key: your-key" \
  -d '{
    "tool_name": "meta_self_improvement_tool",
    "params": {"action": "optimize"},
    "recursive_depth": 2,
    "tools_to_call": ["meta_analyze_tool", "meta_schema_generator"]
  }'
```

### 5. Meta-Research
```bash
curl -X POST http://localhost:8000/meta/research \
  -H "X-API-Key: your-key" \
  -d '{
    "query": "How can research systems improve themselves?",
    "analyze_own_research": true
  }'
```

## Use Cases

1. **Self-Optimization**: BOP analyzes its performance and generates recommendations
2. **Dynamic Adaptation**: Generate schemas for new query types on the fly
3. **Tool Composition**: Create tools that orchestrate other tools
4. **Recursive Problem Solving**: Break complex problems into nested tool calls
5. **Meta-Learning**: Research about research effectiveness
6. **Self-Documentation**: BOP can document its own capabilities

## Limitations

- **Recursion Depth**: Max 3 levels to prevent infinite loops
- **Schema Validation**: Generated schemas should follow existing patterns
- **Meta-Tool Safety**: Meta-tools can modify the system - use with caution
- **Self-Analysis Overhead**: Deep analysis (depth=3) can be slow

## See Also

- `docs/guides/WEB_API_FEATURES.md` - Basic web API features
- `docs/guides/CAPABILITIES_EXPLORATION.md` - Full capabilities overview
- `src/bop/server.py` - Implementation details

