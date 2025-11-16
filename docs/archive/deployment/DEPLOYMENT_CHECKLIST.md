# Deployment Checklist - Tailscale-Only Access

## Pre-Deployment

- [ ] Tailscale auth key in `.env` (for local testing)
- [ ] All API keys set in `.env` (LLM backends, MCP tools)
- [ ] Fly.io CLI installed and logged in
- [ ] Tailscale account set up

## Deployment Steps

### 1. Set Fly.io Secrets

```bash
# LLM Backends
flyctl secrets set OPENAI_API_KEY=sk-... -a bop-wispy-voice-3017
flyctl secrets set ANTHROPIC_API_KEY=sk-ant-... -a bop-wispy-voice-3017
flyctl secrets set GEMINI_API_KEY=... -a bop-wispy-voice-3017

# MCP Tools
flyctl secrets set PERPLEXITY_API_KEY=pplx-... -a bop-wispy-voice-3017
flyctl secrets set FIRECRAWL_API_KEY=fc-... -a bop-wispy-voice-3017
flyctl secrets set TAVILY_API_KEY=tvly-... -a bop-wispy-voice-3017

# Tailscale (from .env)
flyctl secrets set TAILSCALE_AUTHKEY=tskey-... -a bop-wispy-voice-3017
```

### 2. Deploy

```bash
just deploy
# or
flyctl deploy -a bop-wispy-voice-3017
```

### 3. Make Private (Remove Public IPs)

```bash
just deploy-private
# or
./scripts/make_private.sh
```

### 4. Verify Tailscale Connection

```bash
# Check logs
just deploy-logs | grep Tailscale

# Or SSH in
flyctl ssh console -a bop-wispy-voice-3017
tailscale ip -4
exit
```

### 5. Test Deployment

```bash
# Test via Tailscale
just test-deployed

# Or manually
TAILSCALE_IP=$(flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4" | grep "^100\.")
curl http://$TAILSCALE_IP:8080/health
```

## Post-Deployment

- [ ] Health endpoint responds: `curl http://<tailscale-ip>:8080/health`
- [ ] Web UI loads: Open `http://<tailscale-ip>:8080` in browser
- [ ] Chat endpoint works: Test a message
- [ ] Mobile access works: Open on phone via Tailscale
- [ ] Public IPs removed: `flyctl ips list -a bop-wispy-voice-3017`

## Access Methods

### Tailscale (Recommended)

1. Install Tailscale on your device
2. Connect to your Tailscale network
3. Get Tailscale IP: `flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"`
4. Access: `http://<tailscale-ip>:8080`

### Fly Proxy (Development)

```bash
# Terminal 1: Start proxy
flyctl proxy 8080:8080 -a bop-wispy-voice-3017

# Terminal 2: Access locally
curl http://localhost:8080/health
```

## Troubleshooting

### Tailscale Not Connecting

```bash
# Check logs
flyctl logs -a bop-wispy-voice-3017 | grep Tailscale

# Check secret is set
flyctl secrets list -a bop-wispy-voice-3017 | grep TAILSCALE

# SSH and check manually
flyctl ssh console -a bop-wispy-voice-3017
tailscale status
```

### Can't Access via Tailscale

1. Verify Tailscale is connected: `tailscale status | grep bop`
2. Check firewall rules in Tailscale admin console
3. Verify you're on the same Tailscale network
4. Try accessing via hostname: `http://bop-wispy-voice-3017.tail-scale.ts.net:8080`

### Public IPs Still Present

```bash
# List IPs
flyctl ips list -a bop-wispy-voice-3017

# Release manually
flyctl ips release <ip-address> -a bop-wispy-voice-3017
```

## Quick Commands

```bash
# Deploy
just deploy

# Make private
just deploy-private

# Test
just test-tailscale
just test-local
just test-deployed

# View logs
just deploy-logs

# Get Tailscale IP
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"
```

