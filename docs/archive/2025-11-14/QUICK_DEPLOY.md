# Quick Deploy to Fly.io

## One-Command Deploy

```bash
./scripts/deploy_fly.sh
```

## Manual Deploy (5 steps)

### 1. Login (if needed)
```bash
flyctl auth login
```

### 2. Launch App
```bash
flyctl launch --name bop --no-config
# Or if app exists:
# flyctl deploy
```

### 3. Set Secrets
```bash
flyctl secrets set OPENAI_API_KEY=your_key
flyctl secrets set ANTHROPIC_API_KEY=your_key
flyctl secrets set PERPLEXITY_API_KEY=your_key
flyctl secrets set FIRECRAWL_API_KEY=your_key
flyctl secrets set TAVILY_API_KEY=your_key
flyctl secrets set BOP_USE_CONSTRAINTS=true
```

### 4. Deploy
```bash
flyctl deploy
```

### 5. Test
```bash
curl https://bop.fly.dev/health
```

## Your App URL

After deployment:
- **https://bop.fly.dev** (or your custom app name)

## Quick Test

```bash
# Health check
curl https://bop.fly.dev/health

# Chat with constraint solver
curl -X POST https://bop.fly.dev/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is trust?",
    "research": true,
    "use_constraints": true
  }'

# View API docs
open https://bop.fly.dev/docs
```

## Monitor

```bash
# View logs
flyctl logs

# Check status
flyctl status

# View metrics
curl https://bop.fly.dev/metrics | jq
```

## Files Ready

✅ `Dockerfile` - Container configuration
✅ `fly.toml` - Fly.io app config
✅ `.dockerignore` - Build exclusions
✅ `scripts/deploy_fly.sh` - Deploy script

See `FLY_DEPLOY.md` for complete guide.

