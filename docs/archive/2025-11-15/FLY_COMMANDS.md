# Fly.io CLI Commands Reference

## Deployment

### Deploy App
```bash
# Deploy to existing app
flyctl deploy -a bop-wispy-voice-3017

# Deploy with remote builder (faster)
flyctl deploy -a bop-wispy-voice-3017 --remote-only

# Deploy without waiting
flyctl deploy -a bop-wispy-voice-3017 --detach
```

### Check Status
```bash
# App status
flyctl status -a bop-wispy-voice-3017

# Detailed info
flyctl info -a bop-wispy-voice-3017

# List all apps
flyctl apps list
```

## Logs

### View Logs
```bash
# All logs
flyctl logs -a bop-wispy-voice-3017

# Follow logs (like tail -f)
flyctl logs -a bop-wispy-voice-3017 -f

# Filter logs
flyctl logs -a bop-wispy-voice-3017 | grep "constraint"

# Last N lines
flyctl logs -a bop-wispy-voice-3017 --limit 100
```

### Stop Following Logs
- Press `Ctrl+C` to stop following
- Logs will continue streaming until interrupted

## Networking

### IP Addresses
```bash
# List IPs
flyctl ips list -a bop-wispy-voice-3017

# Release public IPv4
flyctl ips release -a bop-wispy-voice-3017 <ip-address>

# Release public IPv6
flyctl ips release6 -a bop-wispy-voice-3017 <ip-address>

# Allocate private IPv6 (Flycast)
flyctl ips allocate-v6 --private -a bop-wispy-voice-3017
```

### Private Network Access
```bash
# Proxy to private network (port forwarding)
flyctl proxy 8080:8080 -a bop-wispy-voice-3017

# Stop proxy: Press Ctrl+C

# Access via localhost while proxy is running
curl http://localhost:8080/health
```

## Secrets

### Manage Secrets
```bash
# List secrets
flyctl secrets list -a bop-wispy-voice-3017

# Set secret
flyctl secrets set KEY=value -a bop-wispy-voice-3017

# Set multiple secrets
flyctl secrets set KEY1=value1 KEY2=value2 -a bop-wispy-voice-3017

# Unset secret
flyctl secrets unset KEY -a bop-wispy-voice-3017
```

## SSH & Debugging

### SSH into Machine
```bash
# SSH console
flyctl ssh console -a bop-wispy-voice-3017

# Execute command
flyctl ssh console -a bop-wispy-voice-3017 -C "python -c 'from bop.constraints import PYSAT_AVAILABLE; print(PYSAT_AVAILABLE)'"
```

## Monitoring

### View Metrics
```bash
# Open dashboard
flyctl dashboard -a bop-wispy-voice-3017

# Or visit: https://fly.io/apps/bop-wispy-voice-3017
```

## Common Workflows

### Full Deployment Cycle
```bash
# 1. Check status
flyctl status -a bop-wispy-voice-3017

# 2. Deploy
flyctl deploy -a bop-wispy-voice-3017

# 3. Watch logs
flyctl logs -a bop-wispy-voice-3017 -f

# 4. Test
curl https://bop-wispy-voice-3017.fly.dev/health
```

### Private Access Workflow
```bash
# Terminal 1: Start proxy
flyctl proxy 8080:8080 -a bop-wispy-voice-3017

# Terminal 2: Make requests
export API_KEY="your-api-key"
curl -H "X-API-Key: $API_KEY" http://localhost:8080/health
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"message": "test"}'
```

### Debugging Failed Deployment
```bash
# 1. Check logs
flyctl logs -a bop-wispy-voice-3017

# 2. SSH and debug
flyctl ssh console -a bop-wispy-voice-3017

# 3. Check secrets
flyctl secrets list -a bop-wispy-voice-3017

# 4. Check status
flyctl status -a bop-wispy-voice-3017
```

## Tips

- **Logs hang?** Use `Ctrl+C` to stop following
- **Build slow?** Use `--remote-only` for faster builds
- **Private access?** Use `flyctl proxy` instead of public IPs
- **Check deployment?** Use `flyctl status` to see machine state
- **View all commands?** Run `flyctl --help` or `flyctl <command> --help`

