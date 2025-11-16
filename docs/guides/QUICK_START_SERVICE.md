# Quick Start: BOP Service with Tailscale

## One-Command Start

```bash
# Start service (auto-detects Tailscale and constraint solver)
./scripts/start_service.sh
```

## Manual Start

### 1. Install Dependencies

```bash
# Install constraint solver
uv sync --extra constraints

# Or install everything
uv sync --extra constraints --extra llm-all
```

### 2. Start Server

```bash
# Start with constraint solver
uv run bop serve --constraints

# Or specify host/port
uv run bop serve --host 0.0.0.0 --port 8000 --constraints
```

### 3. Get Your Tailscale IP

```bash
tailscale ip -4
# Example: 100.116.189.39
```

### 4. Access from Any Device

From any device on your Tailscale network:

```bash
# Replace with your Tailscale IP
TAILSCALE_IP=100.116.189.39

# Test health
curl http://$TAILSCALE_IP:8000/health

# View API docs
open http://$TAILSCALE_IP:8000/docs
```

## Test the Service

### Health Check

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","constraint_solver":true}
```

### Chat Endpoint

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is trust in knowledge graphs?",
    "research": true,
    "use_constraints": true
  }'
```

### Constraint Solver Status

```bash
curl http://localhost:8000/constraints/status
```

### Run Evaluation Comparison

```bash
curl "http://localhost:8000/evaluate/compare?query=test&iterations=3"
```

## Monitor Performance

### View Metrics

```bash
curl http://localhost:8000/metrics | jq
```

### Run Monitoring Script

```bash
# Monitor constraint solver performance
uv run python scripts/monitor_constraints.py \
  --query "What is trust?" \
  --iterations 5
```

## Your Tailscale IP

Your current Tailscale IP: **100.116.189.39**

Access the service from other devices at:
- **API**: `http://100.116.189.39:8000`
- **Docs**: `http://100.116.189.39:8000/docs`
- **Health**: `http://100.116.189.39:8000/health`

## Next Steps

1. **Start the service**: `./scripts/start_service.sh`
2. **Test from another device**: Use your Tailscale IP
3. **Monitor performance**: Use `/metrics` endpoint
4. **Run evaluations**: Use `/evaluate/compare` endpoint
5. **Tune parameters**: Adjust constraints based on results

See `PRODUCTION_SETUP.md` for detailed configuration and `TAILSETUP.md` for Tailscale troubleshooting.

