# Tailscale + Fly.io Private Access Setup

## Overview

This setup uses Tailscale to create a private network connection between your Fly.io app and your devices, eliminating the need for public IPs or API keys for access control.

## Benefits

- **Truly Private**: App only accessible via Tailscale network
- **No Public IPs**: Remove all public IPs from Fly.io app
- **Encrypted**: End-to-end encryption via Tailscale
- **Simple Access**: Access via Tailscale IP (e.g., `bop-wispy-voice-3017.tail-scale.ts.net`)
- **No API Keys Needed**: Network-level security instead

## Setup Steps

### 1. Create Tailscale Auth Key

```bash
# Create a reusable auth key (expires in 90 days by default)
tailscale authkeys add --expiry 90d --reusable --tag tag:fly

# Or create an ephemeral key (expires after first use)
tailscale authkeys add --ephemeral --tag tag:fly

# Save the key - you'll need it for Fly.io secrets
```

### 2. Set Tailscale Secret in Fly.io

```bash
# Set the auth key as a secret
flyctl secrets set TAILSCALE_AUTHKEY=tskey-auth-xxxxx -a bop-wispy-voice-3017

# Also set the app name for Tailscale hostname
flyctl secrets set FLY_APP_NAME=bop-wispy-voice-3017 -a bop-wispy-voice-3017
```

### 3. Update Dockerfile

The Dockerfile needs to include Tailscale. You have two options:

**Option A: Use Tailscale-enabled Dockerfile**
```bash
# Rename the Tailscale Dockerfile
mv Dockerfile Dockerfile.original
mv Dockerfile.tailscale Dockerfile
```

**Option B: Update existing Dockerfile**
- Add Tailscale installation
- Add tailscale-start.sh script
- Update CMD to use the startup script

### 4. Deploy

```bash
# Deploy with Tailscale
flyctl deploy -a bop-wispy-voice-3017
```

### 5. Get Tailscale IP

After deployment, the app will join your Tailscale network:

```bash
# Check Tailscale status
tailscale status | grep bop-wispy-voice-3017

# Or check in Fly.io logs
flyctl logs -a bop-wispy-voice-3017 | grep "Tailscale connected"
```

### 6. Remove Public IPs (Optional but Recommended)

```bash
# List current IPs
flyctl ips list -a bop-wispy-voice-3017

# Release public IPv4
flyctl ips release -a bop-wispy-voice-3017 <ip-address>

# Release public IPv6
flyctl ips release6 -a bop-wispy-voice-3017 <ip-address>
```

## Access Methods

### Via Tailscale Hostname

```bash
# Access via Tailscale hostname
curl https://bop-wispy-voice-3017.tail-scale.ts.net/health

# Or via Tailscale IP
TAILSCALE_IP=$(tailscale status | grep bop-wispy-voice-3017 | awk '{print $1}')
curl http://$TAILSCALE_IP:8080/health
```

### Via Fly.io Proxy (Still Works)

```bash
# Fly.io proxy still works for direct access
flyctl proxy 8080:8080 -a bop-wispy-voice-3017
curl http://localhost:8080/health
```

## Configuration

### Tailscale ACLs (Access Control Lists)

Configure who can access the app in your Tailscale admin console:

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["autogroup:members"],
      "dst": ["tag:fly:8080"]
    }
  ],
  "tagOwners": {
    "tag:fly": ["autogroup:admins"]
  }
}
```

### App Configuration

The app will:
- Join Tailscale on startup
- Get a Tailscale IP address
- Be accessible via `bop-wispy-voice-3017.tail-scale.ts.net`
- Listen on port 8080 (internal)

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
```

### Can't Access via Tailscale

1. **Check Tailscale status**:
   ```bash
   tailscale status | grep bop
   ```

2. **Verify ACLs**: Check Tailscale admin console for access rules

3. **Check app is running**:
   ```bash
   flyctl status -a bop-wispy-voice-3017
   ```

4. **Test connectivity**:
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

1. **No Public Exposure**: App has no public IPs
2. **Network-Level Security**: Only Tailscale network can access
3. **Encrypted Traffic**: All traffic encrypted by Tailscale
4. **Audit Logs**: Tailscale logs all connections
5. **ACL Control**: Fine-grained access control via ACLs

## Comparison: Tailscale vs API Keys

| Feature | Tailscale | API Keys |
|---------|-----------|----------|
| Security | Network-level | Application-level |
| Public IPs | Not needed | Required |
| Encryption | Built-in | HTTPS only |
| Access Control | ACLs | Per-request |
| Audit | Tailscale logs | App logs |
| Complexity | Medium | Low |

## Next Steps

1. **Create auth key**: `tailscale authkeys add --reusable --tag tag:fly`
2. **Set secret**: `flyctl secrets set TAILSCALE_AUTHKEY=...`
3. **Deploy**: `flyctl deploy -a bop-wispy-voice-3017`
4. **Access**: `curl https://bop-wispy-voice-3017.tail-scale.ts.net/health`
5. **Remove public IPs**: `flyctl ips release ...`

## References

- [Tailscale on Fly.io](https://tailscale.com/kb/1282/fly)
- [Tailscale Production Best Practices](https://tailscale.com/kb/1300/production-best-practices)
- [Fly.io Networking](https://fly.io/docs/networking/)

