# Private Deployment Guide

## Security Configuration

The BOP service is configured for private access with API key authentication to protect your API keys.

## Access Methods

### 1. Fly.io Private Network (Recommended)

Access via Fly.io's private network using `fly proxy`:

```bash
# Start proxy (connects to private network)
flyctl proxy 8080:8080 -a bop-wispy-voice-3017

# In another terminal, access via localhost
curl http://localhost:8080/health
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"message": "test", "research": true}'
```

### 2. API Key Authentication

All endpoints except `/health` and `/` require an API key:

```bash
# Set API key secret
flyctl secrets set BOP_API_KEY=your-secure-api-key -a bop-wispy-voice-3017

# Use in requests
curl -X POST https://bop-wispy-voice-3017.fly.dev/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{"message": "test", "research": true}'
```

### 3. Remove Public IPs (Most Secure)

Make the app completely private by removing public IPs:

```bash
# List IPs
flyctl ips list -a bop-wispy-voice-3017

# Release public IPv4
flyctl ips release -a bop-wispy-voice-3017

# Release public IPv6 (if any)
flyctl ips release6 -a bop-wispy-voice-3017
```

After removing public IPs, access only via:
- Fly.io private network (`fly proxy`)
- Fly.io WireGuard VPN
- Other Fly.io apps in same organization

## Setup Steps

### 1. Generate API Key

```bash
# Generate secure API key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Set API Key Secret

```bash
flyctl secrets set BOP_API_KEY=your-generated-key -a bop-wispy-voice-3017
```

### 3. Remove Public IPs (Optional but Recommended)

```bash
# Remove all public IPs
flyctl ips list -a bop-wispy-voice-3017
flyctl ips release -a bop-wispy-voice-3017
```

### 4. Redeploy

```bash
flyctl deploy -a bop-wispy-voice-3017
```

## Usage Examples

### Via Fly Proxy (Private Network)

```bash
# Terminal 1: Start proxy
flyctl proxy 8080:8080 -a bop-wispy-voice-3017

# Terminal 2: Make requests
export API_KEY="your-api-key"

# Health check (no auth required)
curl http://localhost:8080/health

# Chat (requires API key)
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "message": "What is trust?",
    "research": true,
    "use_constraints": true
  }'

# Metrics (requires API key)
curl -H "X-API-Key: $API_KEY" http://localhost:8080/metrics
```

### Via Public URL (with API Key)

If you keep public IPs, use API key authentication:

```bash
export API_KEY="your-api-key"
export APP_URL="https://bop-wispy-voice-3017.fly.dev"

# Health check (public, no auth)
curl $APP_URL/health

# Chat (requires API key)
curl -X POST $APP_URL/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "message": "What is trust?",
    "research": true
  }'
```

## Security Best Practices

1. **Remove Public IPs**: Most secure - only accessible via private network
2. **Use Strong API Keys**: Generate with `secrets.token_urlsafe(32)`
3. **Rotate Keys Regularly**: Update `BOP_API_KEY` secret periodically
4. **Monitor Access**: Check logs for unauthorized attempts
5. **Use HTTPS**: Always use HTTPS when accessing via public URL

## Endpoints

### Public (No Auth Required)
- `GET /` - Service info
- `GET /health` - Health check

### Protected (Requires X-API-Key Header)
- `POST /chat` - Chat endpoint
- `GET /constraints/status` - Constraint solver status
- `POST /constraints/toggle` - Toggle constraint solver
- `GET /metrics` - System metrics
- `GET /evaluate/compare` - Evaluation comparison

## Troubleshooting

### "Invalid or missing API key"
- Check that `BOP_API_KEY` secret is set: `flyctl secrets list -a bop-wispy-voice-3017`
- Verify you're sending `X-API-Key` header
- Check the key matches the secret

### Can't Access After Removing Public IPs
- Use `flyctl proxy` to access via private network
- Or connect to Fly.io WireGuard VPN
- Or access from another Fly.io app in same org

### Proxy Not Working
```bash
# Check app is running
flyctl status -a bop-wispy-voice-3017

# Check proxy connection
flyctl proxy 8080:8080 -a bop-wispy-voice-3017 -v
```

## Current Configuration

- **App Name**: `bop-wispy-voice-3017`
- **URL**: `https://bop-wispy-voice-3017.fly.dev`
- **API Key**: Set via `BOP_API_KEY` secret
- **Public IPs**: Check with `flyctl ips list -a bop-wispy-voice-3017`

