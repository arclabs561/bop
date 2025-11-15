# Tailscale Setup - Complete Guide

## Current Status

⚠️ **Tailscale is not yet configured on BOP**. Follow these steps to enable Tailscale access.

## Quick Setup (5 Steps)

### Step 1: Create Tailscale Auth Key

**Option A: Via Tailscale Admin Console** (Easiest)
1. Go to https://login.tailscale.com/admin/settings/keys
2. Click "Generate auth key"
3. Select:
   - **Reusable**: ✅ Yes
   - **Ephemeral**: ❌ No
   - **Expires in**: 90 days
   - **Tags**: `tag:fly` (optional)
4. Copy the key (starts with `tskey-auth-...`)

**Option B: Via Tailscale CLI** (if installed)
```bash
tailscale authkeys add --expiry 90d --reusable --tag tag:fly
```

### Step 2: Set Auth Key in Fly.io

```bash
# Replace YOUR_AUTH_KEY with the key from Step 1
flyctl secrets set TAILSCALE_AUTHKEY=YOUR_AUTH_KEY -a bop-wispy-voice-3017

# Verify it's set
flyctl secrets list -a bop-wispy-voice-3017 | grep TAILSCALE
```

### Step 3: Verify Dockerfile Has Tailscale

Check if `Dockerfile` includes Tailscale setup. If not, we need to update it.

### Step 4: Start the App

```bash
# Start the app (auto-stop is enabled, so it may be stopped)
flyctl machines start 0807666a672e98 -a bop-wispy-voice-3017

# Or scale to 1 machine
flyctl scale count 1 --yes -a bop-wispy-voice-3017
```

### Step 5: Get Tailscale IP

```bash
# Wait a few seconds for Tailscale to connect, then:
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"
```

**Output example**: `100.64.1.2`

## Access from Your Devices

### On Your Phone

1. **Install Tailscale**:
   - iOS: App Store → "Tailscale"
   - Android: Google Play → "Tailscale"

2. **Sign in** to your Tailscale account

3. **Open browser** and go to:
   ```
   http://<tailscale-ip>:8080/health
   ```
   Example: `http://100.64.1.2:8080/health`

4. **Test API** (using a terminal app or API client):
   ```bash
   curl -X POST http://<tailscale-ip>:8080/chat \
     -H "Content-Type: application/json" \
     -H "X-API-Key: YOUR_API_KEY" \
     -d '{"message": "Hello from phone!", "research": false}'
   ```

### On Your Computer

1. **Install Tailscale**:
   ```bash
   # macOS
   brew install tailscale
   
   # Or download from https://tailscale.com/download
   ```

2. **Sign in** to your Tailscale account

3. **Access in browser**:
   ```
   http://<tailscale-ip>:8080/health
   ```

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

## Using MagicDNS (Easier)

If MagicDNS is enabled in your Tailscale network:

1. **Find machine name** in Tailscale admin console
2. **Use hostname** instead of IP:
   ```
   http://<machine-name>:8080
   ```
   Example: `http://bop-wispy-voice-3017:8080`

## Troubleshooting

### "Tailscale not running" Error

**Check if auth key is set**:
```bash
flyctl secrets list -a bop-wispy-voice-3017 | grep TAILSCALE
```

**If not set**, follow Step 2 above.

**If set but not working**:
```bash
# Check logs
flyctl logs -a bop-wispy-voice-3017 | grep -i tailscale

# Restart app
flyctl apps restart bop-wispy-voice-3017
```

### Can't Connect from Device

1. **Verify Tailscale is connected** on your device (green status)
2. **Check if BOP appears** in your Tailscale network:
   - Open Tailscale admin console
   - Look for `bop-wispy-voice-3017` or similar
3. **Test connectivity**:
   ```bash
   # From your computer
   ping <tailscale-ip>
   ```

### App is Stopped

BOP has auto-stop enabled. Start it:
```bash
flyctl machines start 0807666a672e98 -a bop-wispy-voice-3017
```

Or make a request - it will auto-start:
```bash
curl http://<tailscale-ip>:8080/health
```

## Next Steps

1. ✅ Create Tailscale auth key
2. ✅ Set `TAILSCALE_AUTHKEY` secret
3. ✅ Start the app
4. ✅ Get Tailscale IP
5. ✅ Install Tailscale on your devices
6. ✅ Access BOP from phone/computer

## Full Documentation

- **Detailed Guide**: `TAILSCALE_ACCESS_GUIDE.md`
- **Quick Start**: `TAILSCALE_SETUP_QUICKSTART.md`
- **Original Setup**: `DEPLOYMENT_SETUP_TAILSCALE.md`

