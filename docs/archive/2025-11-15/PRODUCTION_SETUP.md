# BOP Production Setup Guide

## Overview

This guide covers setting up BOP for production use with:
- Constraint solver enabled
- HTTP server for remote access
- Monitoring and evaluation
- Tailscale integration

## Quick Start

### 1. Install Dependencies

```bash
# Install all dependencies including constraint solver
uv sync --extra constraints

# Or install everything
uv sync --extra constraints --extra llm-all
```

### 2. Configure Environment

Create `.env` file:

```bash
# Constraint solver (enabled by default)
BOP_USE_CONSTRAINTS=true

# LLM backends (choose one or more)
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GEMINI_API_KEY=your_key

# MCP tools
PERPLEXITY_API_KEY=your_key
FIRECRAWL_API_KEY=your_key
TAVILY_API_KEY=your_key

# Server configuration
BOP_HOST=0.0.0.0  # Listen on all interfaces for Tailscale
BOP_PORT=8000
```

### 3. Start HTTP Server

```bash
# Start server with constraint solver
uv run bop serve --constraints

# Or specify host/port
uv run bop serve --host 0.0.0.0 --port 8000 --constraints
```

### 4. Access via Tailscale

1. **Get your Tailscale IP**:
   ```bash
   tailscale ip -4
   ```

2. **Access the API**:
   - API: `http://<tailscale-ip>:8000`
   - Docs: `http://<tailscale-ip>:8000/docs`
   - Health: `http://<tailscale-ip>:8000/health`

3. **Test from another device**:
   ```bash
   curl http://<tailscale-ip>:8000/health
   ```

## API Endpoints

### Chat

```bash
POST /chat
Content-Type: application/json

{
  "message": "What is trust in knowledge graphs?",
  "schema": "chain_of_thought",
  "research": true,
  "use_constraints": true
}
```

### Constraint Solver Status

```bash
GET /constraints/status
```

### Toggle Constraint Solver

```bash
POST /constraints/toggle?enabled=true
```

### Metrics

```bash
GET /metrics
```

### Evaluation Comparison

```bash
GET /evaluate/compare?query=test&iterations=5
```

## Monitoring

### View Logs

```bash
# Server logs show constraint solver activity
uv run bop serve --constraints

# Look for:
# - "Constraint solver enabled"
# - "Constraint solver selected X tools"
# - Tool selection traces
```

### Check Metrics

```bash
# Get current metrics
curl http://localhost:8000/metrics

# Check constraint solver status
curl http://localhost:8000/constraints/status
```

### Quality Feedback

```bash
# View quality performance
uv run bop quality --adaptive

# View evaluation history
uv run bop quality --history
```

## Evaluation

### Compare Constraint vs Heuristic

```bash
# Via API
curl "http://localhost:8000/evaluate/compare?query=test&iterations=5"

# Via CLI
uv run bop eval --content-dir content
```

### Run Constraint Tests

```bash
# Run all constraint tests
uv run pytest tests/ -k "constraint" -v

# Run E2E tests
uv run pytest tests/test_constraints_e2e.py -v
```

## Tuning Constraint Parameters

### Adjust Tool Constraints

Edit `src/bop/constraints.py` - `create_default_constraints()`:

```python
def create_default_constraints():
    """Create default tool constraints."""
    return [
        ToolConstraint(
            tool=ToolType.PERPLEXITY_DEEP,
            cost=0.5,  # Adjust cost
            information_gain=0.8,  # Adjust information gain
            latency=3.0,  # Adjust latency
        ),
        # ... other tools
    ]
```

### Adjust Selection Parameters

In `src/bop/orchestrator.py` - `_select_tools_with_constraints()`:

```python
# Adjust minimum information requirement
min_information = 0.5  # Default: 0.5, increase for deeper research

# Adjust for deep queries
if any(word in subproblem_lower for word in ["comprehensive", "deep"]):
    min_information = 0.7  # Higher requirement
```

## Production Checklist

- [ ] Constraint solver installed (`uv sync --extra constraints`)
- [ ] Environment variables configured (`.env` file)
- [ ] `BOP_USE_CONSTRAINTS=true` set
- [ ] HTTP server accessible via Tailscale
- [ ] Monitoring endpoints working (`/health`, `/metrics`)
- [ ] Evaluation comparison tested (`/evaluate/compare`)
- [ ] Logs show constraint solver activity
- [ ] Quality feedback enabled

## Troubleshooting

### Constraint Solver Not Available

```bash
# Check if PySAT is installed
uv run python -c "from bop.constraints import PYSAT_AVAILABLE; print(PYSAT_AVAILABLE)"

# Install if missing
uv sync --extra constraints
```

### Server Not Accessible

1. **Check Tailscale**:
   ```bash
   tailscale status
   tailscale ip -4
   ```

2. **Check Firewall**:
   ```bash
   # macOS
   sudo pfctl -sr | grep 8000
   
   # Linux
   sudo ufw status
   ```

3. **Check Server Logs**:
   ```bash
   uv run bop serve --constraints
   # Look for "Starting BOP server on..."
   ```

### Constraint Solver Not Selecting Tools

1. **Check logs** for "Constraint solver selected" messages
2. **Verify constraints** are not too restrictive
3. **Check fallback** - if constraints fail, heuristics are used
4. **Test directly**:
   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "test", "research": true, "use_constraints": true}'
   ```

## Next Steps

1. **Monitor Performance**: Use `/metrics` endpoint to track usage
2. **Tune Parameters**: Adjust constraints based on real usage
3. **Evaluate Quality**: Compare constraint vs heuristic selection
4. **Scale**: Consider load balancing for multiple users

## Security Notes

- **Tailscale**: Provides encrypted VPN, but restrict CORS in production
- **API Keys**: Never commit `.env` file
- **Access Control**: Consider adding authentication for production
- **Rate Limiting**: Add rate limiting for public endpoints

