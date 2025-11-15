# 🚀 Deployment Ready - Fly.io

## Quick Deploy

```bash
# Option 1: Use deploy script
./scripts/deploy_fly.sh

# Option 2: Manual deploy
fly launch
fly secrets set OPENAI_API_KEY=your_key
fly secrets set ANTHROPIC_API_KEY=your_key
fly secrets set PERPLEXITY_API_KEY=your_key
fly secrets set FIRECRAWL_API_KEY=your_key
fly secrets set TAVILY_API_KEY=your_key
fly secrets set BOP_USE_CONSTRAINTS=true
fly deploy
```

## What's Configured

✅ **Dockerfile** - Multi-stage build with uv, constraint solver, all dependencies
✅ **fly.toml** - Fly.io configuration with health checks, auto-scaling
✅ **Port Configuration** - Uses PORT env var (Fly.io standard)
✅ **Health Checks** - `/health` endpoint for monitoring
✅ **Auto-scaling** - Machines stop when idle, start on demand
✅ **HTTPS** - Automatic SSL/TLS

## Files Created

- `Dockerfile` - Container image definition
- `fly.toml` - Fly.io app configuration
- `.dockerignore` - Docker build exclusions
- `FLY_DEPLOY.md` - Complete deployment guide
- `scripts/deploy_fly.sh` - Quick deploy script

## Next Steps

1. **Set Secrets** (API keys):
   ```bash
   fly secrets set OPENAI_API_KEY=your_key
   fly secrets set ANTHROPIC_API_KEY=your_key
   fly secrets set PERPLEXITY_API_KEY=your_key
   fly secrets set FIRECRAWL_API_KEY=your_key
   fly secrets set TAVILY_API_KEY=your_key
   fly secrets set BOP_USE_CONSTRAINTS=true
   ```

2. **Deploy**:
   ```bash
   fly deploy
   ```

3. **Test**:
   ```bash
   curl https://bop.fly.dev/health
   ```

## App URL

After deployment, your app will be at:
- **https://bop.fly.dev** (or your custom app name)

## Monitoring

```bash
# View logs
fly logs

# Check status
fly status

# View metrics
curl https://bop.fly.dev/metrics
```

## Cost Optimization

- **Auto-stop**: Machines stop when idle (saves money)
- **Auto-start**: Machines start automatically on first request
- **Min machines**: 0 (no cost when idle)
- **Resources**: 512MB RAM, 1 shared CPU (adjustable)

See `FLY_DEPLOY.md` for complete documentation.

