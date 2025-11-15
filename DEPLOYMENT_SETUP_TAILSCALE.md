# BOP Deployment: Tailscale Setup Guide

## Overview

This guide sets up BOP with Tailscale for private, secure access without public IPs.

## Why Tailscale?

- ✅ **No public exposure** - App only accessible via Tailscale network
- ✅ **Mobile access** - Native iOS/Android apps
- ✅ **Simple access** - Works like local network
- ✅ **Encrypted** - End-to-end encryption built-in
- ✅ **Free tier** - Sufficient for personal use

## Setup Steps

### 1. Create Tailscale Auth Key

```bash
# Create a reusable auth key (expires in 90 days)
tailscale authkeys add --expiry 90d --reusable --tag tag:fly

# Save the key (starts with tskey-auth-...)
# Example: tskey-auth-xxxxx-xxxxx
```

**Note**: If you don't have Tailscale CLI installed:
- Install: https://tailscale.com/download
- Or create key in Tailscale admin console: https://login.tailscale.com/admin/settings/keys

### 2. Set Tailscale Secret in Fly.io

```bash
APP_NAME="bop-wispy-voice-3017"

# Set the auth key
flyctl secrets set TAILSCALE_AUTHKEY=tskey-auth-xxxxx -a $APP_NAME

# Verify it's set
flyctl secrets list -a $APP_NAME | grep TAILSCALE
```

### 3. Switch to Tailscale Dockerfile

```bash
# Backup current Dockerfile
cp Dockerfile Dockerfile.backup

# Use Tailscale-enabled Dockerfile
cp Dockerfile.tailscale Dockerfile
```

### 4. Deploy with Tailscale

```bash
# Deploy
flyctl deploy -a bop-wispy-voice-3017 --remote-only

# Watch logs to see Tailscale connection
flyctl logs -a bop-wispy-voice-3017 -f | grep -i tailscale
```

### 5. Get Tailscale IP

After deployment, get the Tailscale IP:

```bash
# Option 1: From Fly.io logs
flyctl logs -a bop-wispy-voice-3017 | grep "Tailscale connected"

# Option 2: SSH into container
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"

# Option 3: From your Tailscale network
tailscale status | grep bop-wispy-voice-3017
```

### 6. Remove Public IPs (Recommended)

```bash
# List current IPs
flyctl ips list -a bop-wispy-voice-3017

# Release public IPv4
flyctl ips release -a bop-wispy-voice-3017

# Release public IPv6 (if any)
flyctl ips release6 -a bop-wispy-voice-3017

# Verify no public IPs remain
flyctl ips list -a bop-wispy-voice-3017
```

## Access Methods

### Via Tailscale Hostname (Recommended)

```bash
# Access via Tailscale hostname
curl http://bop-wispy-voice-3017.tail-scale.ts.net:8080/health

# Or in browser
# http://bop-wispy-voice-3017.tail-scale.ts.net:8080
```

### Via Tailscale IP

```bash
# Get IP
TAILSCALE_IP=$(tailscale status | grep bop-wispy-voice-3017 | awk '{print $1}')

# Access
curl http://$TAILSCALE_IP:8080/health
```

### Via Fly.io Proxy (Development)

```bash
# Terminal 1: Start proxy
flyctl proxy 8080:8080 -a bop-wispy-voice-3017

# Terminal 2: Access locally
curl http://localhost:8080/health
```

## Mobile Access

### iOS

1. Install Tailscale app from App Store
2. Sign in to your Tailscale account
3. Open Safari
4. Navigate to: `http://bop-wispy-voice-3017.tail-scale.ts.net:8080`
5. (Optional) Add to Home Screen for app-like experience

### Android

1. Install Tailscale app from Play Store
2. Sign in to your Tailscale account
3. Open Chrome
4. Navigate to: `http://bop-wispy-voice-3017.tail-scale.ts.net:8080`
5. (Optional) Add to Home Screen for app-like experience

## Troubleshooting

### Tailscale Not Connecting

```bash
# Check logs
flyctl logs -a bop-wispy-voice-3017 | grep -i tailscale

# Verify auth key is set
flyctl secrets list -a bop-wispy-voice-3017 | grep TAILSCALE

# Check Tailscale status in container
flyctl ssh console -a bop-wispy-voice-3017
tailscale status
exit
```

### Can't Access from Device

1. **Verify Tailscale is connected**:
   ```bash
   tailscale status | grep bop
   ```

2. **Check ACLs** (if using Tailscale team):
   - Visit: https://login.tailscale.com/admin/acls
   - Ensure access is allowed

3. **Test connectivity**:
   ```bash
   ping bop-wispy-voice-3017.tail-scale.ts.net
   ```

### Auth Key Expired

```bash
# Create new auth key
tailscale authkeys add --expiry 90d --reusable --tag tag:fly

# Update secret
flyctl secrets set TAILSCALE_AUTHKEY=new-key -a bop-wispy-voice-3017

# Restart app
flyctl apps restart bop-wispy-voice-3017
```

## Security Benefits

1. **No Public Exposure** - App has no public IPs
2. **Network-Level Security** - Only Tailscale network can access
3. **Encrypted Traffic** - All traffic encrypted by Tailscale
4. **Audit Logs** - Tailscale logs all connections
5. **ACL Control** - Fine-grained access control (if using Tailscale team)

## Next Steps

1. ✅ Create Tailscale auth key
2. ✅ Set `TAILSCALE_AUTHKEY` secret
3. ✅ Switch to `Dockerfile.tailscale`
4. ✅ Deploy
5. ✅ Remove public IPs
6. ✅ Test access from mobile device
7. ✅ Update documentation

