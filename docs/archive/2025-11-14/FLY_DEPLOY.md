# Fly.io Deployment Guide

## Quick Deploy

```bash
# 1. Install Fly CLI (if not installed)
curl -L https://fly.io/install.sh | sh

# 2. Login to Fly.io
fly auth login

# 3. Launch the app (creates fly.toml if needed)
fly launch

# 4. Set secrets (API keys)
fly secrets set OPENAI_API_KEY=your_key
fly secrets set ANTHROPIC_API_KEY=your_key
fly secrets set PERPLEXITY_API_KEY=your_key
fly secrets set FIRECRAWL_API_KEY=your_key
fly secrets set TAVILY_API_KEY=your_key

# 5. Deploy
fly deploy
```

## Configuration

### Environment Variables (Secrets)

Set these via `fly secrets set`:

```bash
# Constraint solver (optional, defaults to true)
fly secrets set BOP_USE_CONSTRAINTS=true

# LLM backends (choose one or more)
fly secrets set OPENAI_API_KEY=your_key
fly secrets set ANTHROPIC_API_KEY=your_key
fly secrets set GEMINI_API_KEY=your_key

# MCP tools
fly secrets set PERPLEXITY_API_KEY=your_key
fly secrets set FIRECRAWL_API_KEY=your_key
fly secrets set TAVILY_API_KEY=your_key

# Optional: LLM backend selection
fly secrets set LLM_BACKEND=anthropic
fly secrets set LLM_MODEL=claude-sonnet-4-5
```

### View Current Secrets

```bash
fly secrets list
```

### Update Secrets

```bash
fly secrets set KEY=new_value
```

## Deployment Steps

### 1. Initial Setup

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch (creates fly.toml)
fly launch
# - App name: bop (or choose your own)
# - Region: Choose closest to you (e.g., iad, ord, sjc)
# - PostgreSQL: No (we don't need it)
# - Redis: No (we don't need it)
```

### 2. Configure Secrets

```bash
# Set all required API keys
fly secrets set OPENAI_API_KEY=your_key
fly secrets set ANTHROPIC_API_KEY=your_key
fly secrets set PERPLEXITY_API_KEY=your_key
fly secrets set FIRECRAWL_API_KEY=your_key
fly secrets set TAVILY_API_KEY=your_key

# Enable constraint solver
fly secrets set BOP_USE_CONSTRAINTS=true
```

### 3. Deploy

```bash
# Deploy the app
fly deploy

# Watch logs
fly logs
```

### 4. Verify Deployment

```bash
# Check status
fly status

# Test health endpoint
curl https://bop.fly.dev/health

# View API docs
open https://bop.fly.dev/docs
```

## App Management

### View App Info

```bash
fly status
fly info
```

### View Logs

```bash
# All logs
fly logs

# Follow logs
fly logs -f

# Filter logs
fly logs | grep "constraint"
```

### Scale

```bash
# Scale to 2 instances
fly scale count 2

# Scale memory
fly scale vm shared-cpu-1x --memory 1024
```

### SSH into Instance

```bash
fly ssh console
```

### Restart

```bash
fly apps restart bop
```

## API Access

After deployment, your app will be available at:

```
https://bop.fly.dev
```

### Endpoints

- **Health**: `https://bop.fly.dev/health`
- **API Docs**: `https://bop.fly.dev/docs`
- **Metrics**: `https://bop.fly.dev/metrics`
- **Chat**: `POST https://bop.fly.dev/chat`

### Example Request

```bash
curl -X POST https://bop.fly.dev/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is trust in knowledge graphs?",
    "research": true,
    "use_constraints": true
  }'
```

## Monitoring

### View Metrics

```bash
# Via API
curl https://bop.fly.dev/metrics | jq

# Via Fly.io dashboard
fly dashboard
```

### Check Constraint Solver

```bash
curl https://bop.fly.dev/constraints/status
```

### View Logs

```bash
fly logs | grep "constraint"
```

## Troubleshooting

### Build Fails

```bash
# Check build logs
fly logs --build

# Test Docker build locally
docker build -t bop-test .
docker run -p 8080:8080 bop-test
```

### App Won't Start

```bash
# Check logs
fly logs

# Check status
fly status

# SSH and debug
fly ssh console
```

### Health Check Fails

```bash
# Check health endpoint
curl https://bop.fly.dev/health

# Check logs for errors
fly logs | grep -i error
```

### Constraint Solver Not Working

```bash
# Check if PySAT is installed
fly ssh console
python -c "from bop.constraints import PYSAT_AVAILABLE; print(PYSAT_AVAILABLE)"

# Check environment variable
fly secrets list | grep BOP_USE_CONSTRAINTS
```

### Port Issues

Fly.io uses the `PORT` environment variable (set to 8080 in fly.toml). The server automatically uses this.

## Cost Optimization

### Auto-Stop Machines

The `fly.toml` is configured with:
```toml
auto_stop_machines = true
auto_start_machines = true
min_machines_running = 0
```

This means:
- Machines stop when idle (saves money)
- Machines start automatically on first request
- No machines running when idle (free tier friendly)

### Resource Limits

Current configuration:
- CPU: 1 shared CPU
- Memory: 512 MB

Adjust in `fly.toml`:
```toml
[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512  # Increase if needed
```

## Custom Domain

```bash
# Add custom domain
fly certs add yourdomain.com

# Check certificate status
fly certs show yourdomain.com
```

## Updates

### Redeploy

```bash
# After code changes
fly deploy

# With specific version
fly deploy --image your-image:tag
```

### Rollback

```bash
# List releases
fly releases

# Rollback to previous
fly releases rollback
```

## Security

### Secrets Management

- Never commit secrets to git
- Use `fly secrets set` for all API keys
- Rotate secrets regularly

### CORS

The server currently allows all origins (`*`). For production:

1. Update `src/bop/server.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. Redeploy:
```bash
fly deploy
```

## Performance

### Cold Start

First request after idle period may be slow (machine starting). Subsequent requests are fast.

### Warm Instances

To keep instances warm:
```bash
# Set min_machines_running to 1
fly scale count 1
```

Or update `fly.toml`:
```toml
min_machines_running = 1
```

## Next Steps

1. **Deploy**: `fly deploy`
2. **Test**: `curl https://bop.fly.dev/health`
3. **Monitor**: `fly logs -f`
4. **Scale**: Adjust resources as needed
5. **Custom Domain**: Add your domain

## Support

- Fly.io Docs: https://fly.io/docs
- Fly.io Community: https://community.fly.io
- FastAPI on Fly.io: https://fly.io/docs/python/frameworks/fastapi/

