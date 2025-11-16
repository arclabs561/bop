# Tailscale Quick Access

## Get Your Access IP

Run this command to get BOP's Tailscale IP:

```bash
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"
```

**Output example**: `100.64.1.2`

## Access URLs

Once you have the IP (e.g., `100.64.1.2`):

### On Your Phone
1. Open Tailscale app (ensure connected - green status)
2. Open browser
3. Go to: `http://100.64.1.2:8080/health`

### On Your Computer
```bash
# Health check
curl http://100.64.1.2:8080/health

# Or in browser
# http://100.64.1.2:8080/health
```

## API Usage

```bash
# Replace <tailscale-ip> with your actual IP
curl -X POST http://<tailscale-ip>:8080/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"message": "Hello!", "research": false}'
```

## If IP Not Available Yet

Tailscale may need a few more seconds to connect. Wait 30 seconds and try again:

```bash
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"
```

## Troubleshooting

### Check Tailscale Status
```bash
flyctl logs -a bop-wispy-voice-3017 | grep -i tailscale
```

### Restart App
```bash
flyctl apps restart bop-wispy-voice-3017
```

### Verify Auth Key is Set
```bash
flyctl secrets list -a bop-wispy-voice-3017 | grep TAILSCALE
```

