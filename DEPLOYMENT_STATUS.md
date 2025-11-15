# BOP Deployment Status

## Current Status

**Last Updated**: $(date)

### Deployment
- **App**: `bop-wispy-voice-3017`
- **Region**: `iad`
- **Status**: Check with `flyctl status -a bop-wispy-voice-3017`

### Volumes
- **Cache Volume**: Check with `flyctl volumes list -a bop-wispy-voice-3017`
- **Mount Point**: `/data` (configured in `fly.toml`)

### Security
- **Public IPs**: Removed (private deployment)
- **Access**: Tailscale or Fly.io private network only
- **API Key**: Required for protected endpoints

### Caching
- **Status**: Implemented and ready
- **Volume**: Create with `./scripts/setup_cache_volume.sh`
- **Cache Dir**: `/data/cache` (auto-created on first use)

## Quick Commands

### Check Status
```bash
flyctl status -a bop-wispy-voice-3017
```

### Check Volumes
```bash
flyctl volumes list -a bop-wispy-voice-3017
```

### Check Logs
```bash
flyctl logs -a bop-wispy-voice-3017 --no-tail --limit 50
```

### Verify Cache
```bash
# Check volume mounted
flyctl ssh console -a bop-wispy-voice-3017 -C "ls -la /data"

# Check cache directory
flyctl ssh console -a bop-wispy-voice-3017 -C "ls -la /data/cache"
```

### Access via Tailscale
```bash
# Get Tailscale IP
flyctl ssh console -a bop-wispy-voice-3017 -C "tailscale ip -4"

# Access
curl http://<tailscale-ip>:8080/health
```

### Access via Fly Proxy
```bash
# Terminal 1: Start proxy
flyctl proxy 8080:8080 -a bop-wispy-voice-3017

# Terminal 2: Test
curl http://localhost:8080/health
```

## Next Steps

1. ✅ **Create cache volume** (if not exists)
2. ✅ **Deploy app** (with volume mount)
3. ⏳ **Verify cache** (check `/data/cache` exists)
4. ⏳ **Test caching** (make queries, check cache stats)
5. ⏳ **Set up Tailscale** (if not already done)

