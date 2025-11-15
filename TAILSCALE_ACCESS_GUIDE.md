# Tailscale Access Guide for BOP

## Overview

BOP is deployed on Fly.io with Tailscale integration for private access. This guide explains how to access BOP from your phone or computer using Tailscale.

## Prerequisites

1. **Tailscale account** - Sign up at https://tailscale.com (free tier available)
2. **Tailscale client** installed on your devices:
   - **Phone**: Install Tailscale app from App Store (iOS) or Google Play (Android)
   - **Computer**: Install Tailscale client (macOS, Windows, Linux)

## Step 1: Install Tailscale

### On Your Phone

**iOS**:
1. Open App Store
2. Search for "Tailscale"
3. Install the Tailscale app
4. Open the app and sign in with your Tailscale account

**Android**:
1. Open Google Play Store
2. Search for "Tailscale"
3. Install the Tailscale app
4. Open the app and sign in with your Tailscale account

### On Your Computer

**macOS**:
```bash
# Using Homebrew
brew install tailscale

# Or download from https://tailscale.com/download
```

**Windows**:
- Download from https://tailscale.com/download
- Run the installer
- Sign in with your Tailscale account

**Linux**:
```bash
# Follow instructions at https://tailscale.com/download/linux
```

## Step 2: Get BOP's Tailscale IP

### Option 1: Via Fly.io SSH

```bash
# Get Tailscale IPv4 address
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"

# Get full Tailscale status
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale status"
```

### Option 2: Via Tailscale Admin Console

1. Go to https://login.tailscale.com/admin/machines
2. Look for machine named `bop-wispy-voice-3017` or similar
3. Note the Tailscale IP address (e.g., `100.x.x.x`)

### Option 3: Via Tailscale CLI (if on same network)

```bash
# List all machines
tailscale status

# Find BOP machine
tailscale status | grep bop
```

## Step 3: Access BOP

### On Your Phone

1. **Open Tailscale app** and ensure you're connected (green status)
2. **Open a web browser** (Safari on iOS, Chrome on Android)
3. **Navigate to**:
   ```
   http://<tailscale-ip>:8080
   ```
   Example: `http://100.64.1.2:8080`

4. **Test health endpoint**:
   ```
   http://<tailscale-ip>:8080/health
   ```

5. **Use the API**:
   ```bash
   # Make a chat request
   curl -X POST http://<tailscale-ip>:8080/chat \
     -H "Content-Type: application/json" \
     -H "X-API-Key: YOUR_API_KEY" \
     -d '{"message": "Hello from phone!", "research": false}'
   ```

### On Your Computer

1. **Ensure Tailscale is running** (check system tray/menu bar)
2. **Open a web browser**
3. **Navigate to**:
   ```
   http://<tailscale-ip>:8080
   ```
   Example: `http://100.64.1.2:8080`

4. **Or use curl**:
   ```bash
   # Health check
   curl http://<tailscale-ip>:8080/health

   # Chat request
   curl -X POST http://<tailscale-ip>:8080/chat \
     -H "Content-Type: application/json" \
     -H "X-API-Key: YOUR_API_KEY" \
     -d '{"message": "Hello from computer!", "research": false}'
   ```

## Step 4: Using Tailscale MagicDNS (Easier)

If MagicDNS is enabled in your Tailscale network:

1. **Find the machine name** in Tailscale admin console
2. **Use the hostname** instead of IP:
   ```
   http://<machine-name>:8080
   ```
   Example: `http://bop-wispy-voice-3017:8080`

## Troubleshooting

### Can't Connect

1. **Check Tailscale status**:
   ```bash
   # On your device
   tailscale status
   ```

2. **Verify BOP is in your Tailscale network**:
   - Check Tailscale admin console
   - Ensure BOP machine appears in your network

3. **Check BOP's Tailscale status**:
   ```bash
   flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale status"
   ```

4. **Verify Tailscale auth key is set**:
   ```bash
   flyctl secrets list -a bop-wispy-voice-3017 | grep TAILSCALE
   ```

### Tailscale Not Running on BOP

If Tailscale isn't running on BOP:

1. **Check if auth key is set**:
   ```bash
   flyctl secrets list -a bop-wispy-voice-3017 | grep TAILSCALE
   ```

2. **Set Tailscale auth key** (if not set):
   ```bash
   # Generate a reusable auth key
   # Go to https://login.tailscale.com/admin/settings/keys
   # Create a reusable auth key
   
   # Set it as a secret
   flyctl secrets set TAILSCALE_AUTHKEY=tskey-auth-xxxxx -a bop-wispy-voice-3017
   ```

3. **Restart the app**:
   ```bash
   flyctl apps restart bop-wispy-voice-3017
   ```

### Connection Timeout

1. **Check if app is running**:
   ```bash
   flyctl status -a bop-wispy-voice-3017
   ```

2. **Check if port 8080 is accessible**:
   ```bash
   flyctl ssh console -a bop-wispy-voice-3017 -C "netstat -tuln | grep 8080"
   ```

3. **Verify firewall rules** (Tailscale should handle this automatically)

### Can't Find BOP in Tailscale Network

1. **Check Tailscale auth key**:
   ```bash
   flyctl secrets list -a bop-wispy-voice-3017 | grep TAILSCALE
   ```

2. **Verify auth key is valid**:
   - Go to https://login.tailscale.com/admin/settings/keys
   - Check if key is still active

3. **Regenerate auth key if needed**:
   - Create new reusable auth key
   - Update secret: `flyctl secrets set TAILSCALE_AUTHKEY=tskey-auth-xxxxx -a bop-wispy-voice-3017`
   - Restart app: `flyctl apps restart bop-wispy-voice-3017`

## Quick Reference

### Get BOP's Tailscale IP
```bash
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"
```

### Test Connection
```bash
# From your computer (with Tailscale running)
curl http://<tailscale-ip>:8080/health
```

### Access in Browser
```
http://<tailscale-ip>:8080/health
```

### Make API Request
```bash
curl -X POST http://<tailscale-ip>:8080/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"message": "test", "research": false}'
```

## Security Notes

- ✅ **Private Network**: BOP is only accessible via Tailscale (no public IPs)
- ✅ **Encrypted**: All traffic is encrypted via Tailscale's WireGuard VPN
- ✅ **Authentication**: API endpoints still require API key
- ✅ **No Public Exposure**: BOP is not accessible from the public internet

## Next Steps

1. Install Tailscale on your devices
2. Get BOP's Tailscale IP
3. Access BOP via `http://<tailscale-ip>:8080`
4. Use the API with your API key

Enjoy private, secure access to BOP from anywhere! 🚀

