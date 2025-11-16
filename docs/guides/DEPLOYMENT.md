# BOP Deployment Guide

Complete guide for deploying BOP to Fly.io with Tailscale integration and API authentication.

## Quick Start

```bash
# One-command deployment (includes validation and verification)
./scripts/deploy_fly.sh

# Or manually:
flyctl deploy -a bop-wispy-voice-3017
```

## Prerequisites

1. **Fly.io account** - Sign up at [fly.io](https://fly.io)
2. **Fly CLI** - Install: `curl -L https://fly.io/install.sh | sh`
3. **API Keys** - LLM backends (OpenAI, Anthropic, Google) and MCP tools
4. **Tailscale account** (optional) - For private network access

## Deployment Steps

### 1. Login to Fly.io

```bash
flyctl auth login
```

### 2. Validate Secrets (Recommended)

Before deploying, validate that required secrets are set:

```bash
./scripts/validate_secrets.sh
```

This checks for:
- At least one LLM backend (OpenAI, Anthropic, or Gemini)
- Optional MCP tools (Perplexity, Firecrawl, Tavily)
- Optional API authentication key
- Optional Tailscale auth key

### 3. Set Required Secrets

```bash
APP_NAME="bop-wispy-voice-3017"

# LLM Backends (at least one required)
flyctl secrets set OPENAI_API_KEY=sk-... -a $APP_NAME
flyctl secrets set ANTHROPIC_API_KEY=sk-ant-... -a $APP_NAME
flyctl secrets set GEMINI_API_KEY=... -a $APP_NAME

# MCP Tools (optional but recommended)
flyctl secrets set PERPLEXITY_API_KEY=pplx-... -a $APP_NAME
flyctl secrets set FIRECRAWL_API_KEY=fc-... -a $APP_NAME
flyctl secrets set TAVILY_API_KEY=tvly-... -a $APP_NAME

# API Authentication (optional but recommended for production)
flyctl secrets set BOP_API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))") -a $APP_NAME

# Tailscale (optional, for private network access)
flyctl secrets set TAILSCALE_AUTHKEY=tskey-... -a $APP_NAME
```

### 4. Deploy

```bash
# Using deploy script (recommended - includes validation and verification)
./scripts/deploy_fly.sh

# Or manually
flyctl deploy -a bop-wispy-voice-3017 --remote-only
```

### 5. Verify Deployment

After deployment, verify everything works:

```bash
./scripts/verify_deployment.sh
```

This checks:
- App is running
- Health endpoint responds
- API endpoints are accessible
- Constraint solver is working
- Public IP configuration

## Access Methods

### 1. Public URL (HTTPS)

```bash
# Get your app URL
flyctl apps open -a bop-wispy-voice-3017

# Access: https://bop-wispy-voice-3017.fly.dev
```

**Note**: If `BOP_API_KEY` is set, protected endpoints require the `X-API-Key` header:

```bash
export API_KEY="your-api-key"
curl -H "X-API-Key: $API_KEY" https://bop-wispy-voice-3017.fly.dev/health
```

### 2. Tailscale Private Network (Recommended)

1. **Get Tailscale IP**:
   ```bash
   flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"
   ```

2. **Access from any Tailscale device**:
   - Phone: `http://<tailscale-ip>:8080`
   - Desktop: `http://<tailscale-ip>:8080`
   - No API key needed (private network)

### 3. Fly Proxy (Local Development)

```bash
# Terminal 1: Start proxy
flyctl proxy 8080:8080 -a bop-wispy-voice-3017

# Terminal 2: Access locally
curl http://localhost:8080/health
```

## Security Configuration

### API Key Authentication

All endpoints except `/health` and `/` require API key authentication when `BOP_API_KEY` is set:

```bash
# Generate secure API key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Set as secret
flyctl secrets set BOP_API_KEY=your-generated-key -a bop-wispy-voice-3017

# Use in requests
curl -H "X-API-Key: your-generated-key" https://bop-wispy-voice-3017.fly.dev/chat
```

### Private Deployment

Make the app completely private by removing public IPs:

```bash
./scripts/make_private.sh
# or
flyctl ips release -a bop-wispy-voice-3017
```

After removing public IPs, access only via:
- Fly.io private network (`flyctl proxy`)
- Fly.io WireGuard VPN
- Tailscale (if configured)
- Other Fly.io apps in same organization

## Monitoring

### Health Check

```bash
curl https://bop-wispy-voice-3017.fly.dev/health
# Response: {"status":"healthy","constraint_solver":true}
```

### Logs

```bash
# View logs
flyctl logs -a bop-wispy-voice-3017 --no-tail

# Follow logs
flyctl logs -a bop-wispy-voice-3017 -f

# Filter logs
flyctl logs -a bop-wispy-voice-3017 | grep "constraint"
```

### Status

```bash
# App status
flyctl status -a bop-wispy-voice-3017

# Detailed info
flyctl info -a bop-wispy-voice-3017

# Dashboard
flyctl dashboard -a bop-wispy-voice-3017
```

### Metrics

```bash
# Get metrics (requires API key if set)
curl -H "X-API-Key: your-key" \
  https://bop-wispy-voice-3017.fly.dev/metrics
```

## Scaling

### Auto-scaling

Fly.io automatically scales based on:
- HTTP traffic
- Machine configuration
- Auto-start/stop settings

Current configuration (`fly.toml`):
```toml
auto_stop_machines = 'stop'
auto_start_machines = true
min_machines_running = 0
```

### Manual Scaling

```bash
# Scale to 2 machines
flyctl scale count 2 -a bop-wispy-voice-3017

# Scale memory
flyctl scale memory 1024 -a bop-wispy-voice-3017
```

## Updates

### Deploy Updates

```bash
# Deploy latest code
flyctl deploy -a bop-wispy-voice-3017

# Deploy with remote build (faster)
flyctl deploy -a bop-wispy-voice-3017 --remote-only
```

### Rollback

```bash
# List releases
flyctl releases -a bop-wispy-voice-3017

# Rollback to previous release
flyctl releases rollback <release-id> -a bop-wispy-voice-3017
```

## Troubleshooting

### App Won't Start

```bash
# Check status
flyctl status -a bop-wispy-voice-3017

# View logs
flyctl logs -a bop-wispy-voice-3017 --no-tail

# SSH into machine
flyctl ssh console -a bop-wispy-voice-3017
```

### Health Check Fails

```bash
# Check health endpoint
curl https://bop-wispy-voice-3017.fly.dev/health

# Check logs for errors
flyctl logs -a bop-wispy-voice-3017 | grep -i error
```

### API Key Issues

If endpoints return 401:
1. Check `BOP_API_KEY` secret is set: `flyctl secrets list -a bop-wispy-voice-3017`
2. Include `X-API-Key` header in requests
3. Or remove `BOP_API_KEY` secret for public access (private network only)

### Tailscale Not Connecting

```bash
# Check auth key is set
flyctl secrets list -a bop-wispy-voice-3017 | grep TAILSCALE

# Verify Tailscale is running
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale status"

# Check firewall rules in Tailscale admin console
```

### Build Fails

```bash
# Check build logs
flyctl logs -a bop-wispy-voice-3017 --build

# Test Docker build locally
docker build -t bop-test .
docker run -p 8080:8080 bop-test
```

## Endpoints

### Public (No Auth Required)
- `GET /` - Service info
- `GET /health` - Health check

### Protected (Requires X-API-Key Header if BOP_API_KEY is set)
- `POST /chat` - Chat endpoint
- `GET /constraints/status` - Constraint solver status
- `POST /constraints/toggle` - Toggle constraint solver
- `GET /metrics` - System metrics
- `GET /evaluate/compare` - Evaluation comparison

## Mobile Access

### iOS Safari

1. Open Safari on iPhone
2. Navigate to your BOP URL (Tailscale IP or Fly.io URL)
3. Tap Share → Add to Home Screen
4. App appears as native app icon

### Android Chrome

1. Open Chrome on Android
2. Navigate to your BOP URL
3. Tap Menu → Add to Home Screen
4. App appears as native app icon

### PWA Features

The web interface includes:
- Mobile-optimized layout
- Touch-friendly controls
- Offline detection
- Smooth animations
- Dark mode support

## Cost Optimization

- **Auto-stop machines** - Saves costs when idle
- **Shared CPU** - Sufficient for most workloads
- **Minimal memory** - Start with 512MB, scale if needed
- **Single region** - Deploy in one region to reduce costs

## Security Best Practices

1. **Use Tailscale for Private Access** - Most secure, no public exposure
2. **Set Strong API Keys** - Use `secrets.token_urlsafe(32)`
3. **Rotate Keys Regularly** - Update secrets periodically
4. **Monitor Access** - Check logs for unauthorized attempts
5. **Use HTTPS** - Always use HTTPS for public URLs
6. **Remove Public IPs** - For maximum security, use private deployment

## Quick Reference

### Common Commands

```bash
# Deploy
./scripts/deploy_fly.sh

# Validate secrets
./scripts/validate_secrets.sh

# Verify deployment
./scripts/verify_deployment.sh

# Make private
./scripts/make_private.sh

# View logs
flyctl logs -a bop-wispy-voice-3017 --no-tail

# Check status
flyctl status -a bop-wispy-voice-3017

# SSH console
flyctl ssh console -a bop-wispy-voice-3017
```

### App Information

- **App Name**: `bop-wispy-voice-3017`
- **URL**: `https://bop-wispy-voice-3017.fly.dev`
- **Region**: `iad` (Washington, D.C.)
- **Resources**: 1 shared CPU, 512MB RAM

## Support

- **Fly.io Docs**: https://fly.io/docs
- **Tailscale Docs**: https://tailscale.com/kb
- **BOP Issues**: Check project repository
