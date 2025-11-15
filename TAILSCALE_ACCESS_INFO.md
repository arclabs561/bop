# BOP Tailscale Access Information

## Current Status

**Last Updated**: $(date)

### Tailscale Configuration
- ✅ **Auth Key**: Set in Fly.io secrets
- ✅ **Dockerfile**: Includes Tailscale
- ⏳ **Status**: Starting/Connecting

### Access Information

**Tailscale IP**: Get with:
```bash
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"
```

**Access URL** (once IP is available):
```
http://<tailscale-ip>:8080
```

**Health Check**:
```
http://<tailscale-ip>:8080/health
```

## Quick Access Commands

### Get Tailscale IP
```bash
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"
```

### Test Connection (from your computer with Tailscale)
```bash
# Replace <tailscale-ip> with actual IP
curl http://<tailscale-ip>:8080/health
```

### Check Tailscale Status
```bash
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale status"
```

## Device Setup

### Phone
1. Install Tailscale app
2. Sign in to your Tailscale account
3. Open browser: `http://<tailscale-ip>:8080/health`

### Computer
1. Install Tailscale client
2. Sign in to your Tailscale account
3. Access: `http://<tailscale-ip>:8080/health`

## Troubleshooting

### If Tailscale IP Not Found
```bash
# Check if app is running
flyctl status -a bop-wispy-voice-3017

# Check Tailscale logs
flyctl logs -a bop-wispy-voice-3017 | grep -i tailscale

# Restart if needed
flyctl apps restart bop-wispy-voice-3017
```

### If Can't Connect from Device
1. Verify Tailscale is connected on your device (green status)
2. Check if BOP appears in Tailscale admin console
3. Test ping: `ping <tailscale-ip>`

