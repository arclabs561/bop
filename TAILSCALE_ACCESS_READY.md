# Tailscale Access - Ready!

## Current Status

✅ **Tailscale Auth Key**: Set in Fly.io secrets  
✅ **App**: Running and healthy  
⏳ **Tailscale**: Connecting (may take 30-60 seconds)

## Get Your Access IP

Run this command to get BOP's Tailscale IP:

```bash
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"
```

**Wait 30-60 seconds** after app starts for Tailscale to connect, then run the command above.

## Access Instructions

### On Your Phone

1. **Install Tailscale**:
   - iOS: App Store → Search "Tailscale" → Install
   - Android: Google Play → Search "Tailscale" → Install

2. **Sign In**:
   - Open Tailscale app
   - Sign in with your Tailscale account
   - Wait for connection (green status)

3. **Access BOP**:
   - Open browser (Safari/Chrome)
   - Go to: `http://<tailscale-ip>:8080/health`
   - Example: `http://100.64.1.2:8080/health`

### On Your Computer

1. **Install Tailscale**:
   ```bash
   # macOS
   brew install tailscale
   
   # Or download from https://tailscale.com/download
   ```

2. **Sign In**:
   - Open Tailscale client
   - Sign in with your Tailscale account
   - Wait for connection (green status in menu bar)

3. **Access BOP**:
   ```bash
   # Health check
   curl http://<tailscale-ip>:8080/health
   
   # Or in browser
   # http://<tailscale-ip>:8080/health
   ```

## API Usage

Once you have the Tailscale IP:

```bash
# Health check (no auth required)
curl http://<tailscale-ip>:8080/health

# Chat request (requires API key)
curl -X POST http://<tailscale-ip>:8080/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"message": "Hello from Tailscale!", "research": false}'
```

## Troubleshooting

### If Tailscale IP Not Available Yet

Wait 30-60 seconds after app starts, then check:

```bash
# Check Tailscale status
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale status"

# Check logs (use --no-tail to avoid hanging!)
flyctl logs -a bop-wispy-voice-3017 --no-tail | grep -i tailscale
```

### If Can't Connect from Device

1. **Verify Tailscale is connected** on your device (green status)
2. **Check if BOP appears** in Tailscale admin console: https://login.tailscale.com/admin/machines
3. **Test connectivity**:
   ```bash
   # From your computer
   ping <tailscale-ip>
   ```

### App Stopped

BOP has auto-stop enabled. Start it:

```bash
flyctl machines start 0807666a672e98 -a bop-wispy-voice-3017
```

Or make a request - it will auto-start.

## Quick Reference

```bash
# Get Tailscale IP
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"

# Check status
flyctl status -a bop-wispy-voice-3017

# Check logs (use --no-tail!)
flyctl logs -a bop-wispy-voice-3017 --no-tail | grep -i tailscale
```

## Important: flyctl logs Usage

**Always use `--no-tail`** to avoid hanging:

```bash
# ✅ Correct (returns immediately)
flyctl logs -a bop-wispy-voice-3017 --no-tail

# ❌ Wrong (hangs forever)
flyctl logs -a bop-wispy-voice-3017
```

See `FLYCTL_LOGS_USAGE.md` for complete guide.

