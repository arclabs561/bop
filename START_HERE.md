# 🚀 BOP Service - Start Here

## Quick Start Options

### Option 1: Local with Tailscale (30 seconds)

```bash
# 1. Start the service
./scripts/start_service.sh

# 2. From another device (on Tailscale), test:
curl http://100.116.189.39:8000/health
```

### Option 2: Deploy to Fly.io (5 minutes)

```bash
# 1. Install Fly CLI (if needed)
curl -L https://fly.io/install.sh | sh

# 2. Deploy
./scripts/deploy_fly.sh

# 3. Test
curl https://bop.fly.dev/health
```

See `FLY_DEPLOY.md` for detailed Fly.io deployment guide.

## What's Ready

✅ **HTTP Server** - FastAPI server with constraint solver
✅ **Tailscale Integration** - Access from any Tailscale device  
✅ **Monitoring** - Metrics and performance tracking
✅ **Evaluation** - Compare constraint vs heuristic selection
✅ **Documentation** - Complete setup guides

## Your Tailscale IP

**100.116.189.39**

Access from any Tailscale device:
- **API**: `http://100.116.189.39:8000`
- **Docs**: `http://100.116.189.39:8000/docs` (Interactive API docs)
- **Health**: `http://100.116.189.39:8000/health`

## Quick Test

### From Server Machine

```bash
# Start server
uv run bop serve --constraints

# In another terminal, test:
curl http://localhost:8000/health
```

### From Another Device (Tailscale)

```bash
# Replace with your Tailscale IP
curl http://100.116.189.39:8000/health

# Should return:
# {"status":"healthy","constraint_solver":true}
```

## Example API Calls

### Chat with Constraint Solver

```bash
curl -X POST http://100.116.189.39:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is trust in knowledge graphs?",
    "research": true,
    "use_constraints": true
  }'
```

### Check Metrics

```bash
curl http://100.116.189.39:8000/metrics | jq
```

### Compare Constraint vs Heuristic

```bash
curl "http://100.116.189.39:8000/evaluate/compare?query=test&iterations=3" | jq
```

## Documentation

- **`QUICK_START_SERVICE.md`** - Quick start guide
- **`PRODUCTION_SETUP.md`** - Full production setup
- **`TAILSETUP.md`** - Tailscale configuration
- **`PRODUCTION_NEXT_STEPS.md`** - What's been completed

## Next Steps

1. **Start the service**: `./scripts/start_service.sh`
2. **Test from another device**: Use your Tailscale IP
3. **Monitor performance**: Check `/metrics` endpoint
4. **Run evaluations**: Use `/evaluate/compare` endpoint
5. **Tune parameters**: Adjust constraints based on results

## Troubleshooting

**Server won't start?**
- Check: `uv sync --extra constraints`
- Check: Port 8000 available
- Check: `.env` file configured

**Can't access from other device?**
- Check: Tailscale connected (`tailscale status`)
- Check: Firewall allows port 8000
- Check: Using correct Tailscale IP

**Constraint solver not working?**
- Check: `uv sync --extra constraints`
- Check: `BOP_USE_CONSTRAINTS=true` in `.env`
- Check: Server logs for errors

See `TAILSETUP.md` for detailed troubleshooting.

