# Tailscale Setup for BOP Service

## Quick Setup

### 1. Install Tailscale (if not already installed)

**macOS**:
```bash
brew install tailscale
# Or download from https://tailscale.com/download
```

**Linux**:
```bash
# Ubuntu/Debian
curl -fsSL https://tailscale.com/install.sh | sh

# Or use package manager
sudo apt install tailscale
```

### 2. Start Tailscale

```bash
# Start Tailscale service
sudo tailscale up

# Or on macOS (if installed via Homebrew)
tailscale up
```

### 3. Get Your Tailscale IP

```bash
tailscale ip -4
# Example output: 100.x.x.x
```

### 4. Start BOP Server

```bash
# Start server (listens on all interfaces for Tailscale)
uv run bop serve --host 0.0.0.0 --port 8000 --constraints
```

### 5. Access from Other Devices

From any device on your Tailscale network:

```bash
# Get the Tailscale IP from the server machine
TAILSCALE_IP=$(tailscale ip -4)

# Test health endpoint
curl http://${TAILSCALE_IP}:8000/health

# Access API docs
open http://${TAILSCALE_IP}:8000/docs
```

## Testing Access

### From Server Machine

```bash
# Test locally
curl http://localhost:8000/health

# Test via Tailscale IP
curl http://$(tailscale ip -4):8000/health
```

### From Another Device

```bash
# Replace with your server's Tailscale IP
curl http://100.x.x.x:8000/health

# Should return:
# {"status":"healthy","constraint_solver":true}
```

## Example Usage

### Chat via API

```bash
# From any Tailscale device
curl -X POST http://100.x.x.x:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is trust in knowledge graphs?",
    "research": true,
    "use_constraints": true
  }'
```

### Check Constraint Solver Status

```bash
curl http://100.x.x.x:8000/constraints/status
```

### Run Evaluation Comparison

```bash
curl "http://100.x.x.x:8000/evaluate/compare?query=test&iterations=5"
```

## Troubleshooting

### Can't Access from Other Devices

1. **Check Tailscale Status**:
   ```bash
   tailscale status
   # Should show all devices connected
   ```

2. **Check Firewall**:
   ```bash
   # macOS - check if port 8000 is blocked
   # Linux - check ufw/iptables
   sudo ufw status
   sudo ufw allow 8000/tcp
   ```

3. **Check Server is Listening**:
   ```bash
   # On server machine
   netstat -an | grep 8000
   # Should show 0.0.0.0:8000 LISTEN
   ```

4. **Test Locally First**:
   ```bash
   # On server machine
   curl http://localhost:8000/health
   # Should work before testing from other devices
   ```

### Server Not Starting

1. **Check Port Availability**:
   ```bash
   lsof -i :8000
   # If something is using port 8000, change it:
   uv run bop serve --port 8001
   ```

2. **Check Dependencies**:
   ```bash
   uv sync --extra constraints
   ```

### Constraint Solver Not Working

1. **Check Installation**:
   ```bash
   uv run python -c "from bop.constraints import PYSAT_AVAILABLE; print(PYSAT_AVAILABLE)"
   # Should print: True
   ```

2. **Check Environment**:
   ```bash
   echo $BOP_USE_CONSTRAINTS
   # Should be: true
   ```

## Security Notes

- **Tailscale provides encryption** - traffic is encrypted between devices
- **CORS is open** - in production, restrict to Tailscale network IPs
- **No authentication** - consider adding API keys for production
- **Firewall** - ensure only Tailscale network can access

## Production Recommendations

1. **Add Authentication**:
   - API keys
   - JWT tokens
   - Tailscale ACLs

2. **Restrict CORS**:
   - Only allow Tailscale IP ranges
   - Remove wildcard `*` origins

3. **Rate Limiting**:
   - Add rate limiting middleware
   - Prevent abuse

4. **Monitoring**:
   - Use `/metrics` endpoint
   - Set up alerts
   - Log all requests

5. **Backup**:
   - Regular backups of quality history
   - Session data
   - Evaluation results

