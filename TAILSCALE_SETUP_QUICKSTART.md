# Tailscale Setup Quickstart

## Quick Setup (5 minutes)

### 1. Install Tailscale

**Phone**:
- iOS: App Store → Search "Tailscale" → Install
- Android: Google Play → Search "Tailscale" → Install

**Computer**:
```bash
# macOS
brew install tailscale

# Or download from https://tailscale.com/download
```

### 2. Sign In to Tailscale

1. Open Tailscale app/client
2. Sign in with your account (or create one at https://tailscale.com)
3. Wait for connection (green status)

### 3. Get BOP's Tailscale IP

```bash
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"
```

**Output example**: `100.64.1.2`

### 4. Access BOP

**In Browser**:
```
http://100.64.1.2:8080/health
```

**With curl**:
```bash
curl http://100.64.1.2:8080/health
```

## If Tailscale Not Working on BOP

### Check Status
```bash
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale status"
```

### Set Auth Key (if missing)
```bash
# 1. Get auth key from https://login.tailscale.com/admin/settings/keys
# 2. Create reusable auth key
# 3. Set it:
flyctl secrets set TAILSCALE_AUTHKEY=tskey-auth-xxxxx -a bop-wispy-voice-3017

# 4. Restart:
flyctl apps restart bop-wispy-voice-3017
```

## That's It!

Once connected, you can access BOP from any device on your Tailscale network.

**Full guide**: See `TAILSCALE_ACCESS_GUIDE.md` for detailed instructions.

