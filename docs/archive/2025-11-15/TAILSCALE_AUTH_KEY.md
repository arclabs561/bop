# Creating Tailscale Auth Key

## Via Web Console (Recommended)

1. Go to https://login.tailscale.com/admin/settings/keys
2. Click "Generate auth key"
3. Configure:
   - **Description**: "Fly.io BOP service"
   - **Reusable**: ✅ Yes (or Ephemeral for one-time use)
   - **Expiry**: 90 days (or your preference)
   - **Tags**: `tag:fly` (optional, for ACLs)
4. Copy the generated key (starts with `tskey-auth-`)

## Via API (Alternative)

```bash
# Using Tailscale API
curl -X POST "https://api.tailscale.com/api/v2/tailnet/$TAILNET/keys" \
  -H "Authorization: Bearer $TAILSCALE_API_KEY" \
  -d '{
    "capabilities": {
      "devices": {
        "create": {
          "reusable": true,
          "ephemeral": false
        }
      }
    },
    "expirySeconds": 7776000,
    "description": "Fly.io BOP service"
  }'
```

## Set in Fly.io

```bash
# Set the auth key as a secret
flyctl secrets set TAILSCALE_AUTHKEY=tskey-auth-xxxxx -a bop-wispy-voice-3017

# Verify it's set
flyctl secrets list -a bop-wispy-voice-3017 | grep TAILSCALE
```

## Security Notes

- **Reusable keys**: Can be used multiple times (good for deployments)
- **Ephemeral keys**: Single-use, expire after first use (more secure)
- **Expiry**: Set appropriate expiry (90 days is common)
- **Tags**: Use tags for ACL-based access control
- **Rotate**: Regularly rotate keys for security

## Current Setup

After creating the key, set it:
```bash
flyctl secrets set TAILSCALE_AUTHKEY=your-key-here -a bop-wispy-voice-3017
```

Then redeploy:
```bash
flyctl deploy -a bop-wispy-voice-3017
```

