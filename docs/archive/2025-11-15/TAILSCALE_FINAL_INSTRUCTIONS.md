# Tailscale Access - Final Instructions

## Setup Complete ✅

- ✅ Tailscale auth key set in Fly.io secrets
- ✅ App running
- ⏳ Tailscale connecting (30-60 seconds after restart)

## Get Your Access IP

**Wait 30-60 seconds** after the app starts, then run:

```bash
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"
```

**Output example**: `100.64.1.2`

## Access from Your Devices

### Phone Setup

1. **Install Tailscale**:
   - iOS: App Store → "Tailscale"
   - Android: Google Play → "Tailscale"

2. **Sign In**:
   - Open Tailscale app
   - Sign in with your Tailscale account
   - Wait for green "Connected" status

3. **Access BOP**:
   - Open browser
   - Go to: `http://<tailscale-ip>:8080/health`
   - Example: `http://100.64.1.2:8080/health`

### Computer Setup

1. **Install Tailscale**:
   ```bash
   # macOS
   brew install tailscale
   
   # Or download from https://tailscale.com/download
   ```

2. **Sign In**:
   - Open Tailscale client
   - Sign in with your Tailscale account
   - Check menu bar/system tray for green status

3. **Access BOP**:
   ```bash
   # Replace <tailscale-ip> with actual IP
   curl http://<tailscale-ip>:8080/health
   ```

## If Tailscale IP Not Available

### Check Status
```bash
# Check if app is running
flyctl status -a bop-wispy-voice-3017

# Check Tailscale status (use --no-tail!)
flyctl logs -a bop-wispy-voice-3017 --no-tail | grep -i tailscale

# Check Tailscale daemon
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale status"
```

### Restart App
```bash
flyctl apps restart bop-wispy-voice-3017
```

Then wait 30-60 seconds and check again.

## Important: flyctl logs

**Always use `--no-tail`** to avoid hanging:

```bash
# ✅ Correct
flyctl logs -a bop-wispy-voice-3017 --no-tail

# ❌ Wrong (hangs forever)
flyctl logs -a bop-wispy-voice-3017
```

## Quick Commands

```bash
# Get Tailscale IP
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"

# Check app status
flyctl status -a bop-wispy-voice-3017

# Check logs (use --no-tail!)
flyctl logs -a bop-wispy-voice-3017 --no-tail | tail -20
```

## Once Connected

You'll be able to access BOP from any device on your Tailscale network:

- **Health**: `http://<tailscale-ip>:8080/health`
- **API**: `http://<tailscale-ip>:8080/chat`
- **Metrics**: `http://<tailscale-ip>:8080/metrics` (requires API key)

All traffic is encrypted and private - no public internet exposure!

