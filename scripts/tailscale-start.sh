#!/bin/bash
# Start Tailscale and then the BOP server
# Based on Fly.io + Tailscale best practices
# Loads TAILSCALE_AUTHKEY from .env file if not set in environment

set -e

echo "🚀 Starting BOP service..."

# Load .env file if it exists (for local development)
if [ -f .env ] && [ -z "$TAILSCALE_AUTHKEY" ]; then
    echo "📄 Loading TAILSCALE_AUTHKEY from .env file..."
    # Try both TAILSCALE_AUTHKEY and TAILSCALE_AUTH_KEY
    if grep -q "^TAILSCALE_AUTHKEY=" .env; then
        export $(grep -v '^#' .env | grep -v '^$' | grep "^TAILSCALE_AUTHKEY=" | xargs)
    elif grep -q "^TAILSCALE_AUTH_KEY=" .env; then
        # Map TAILSCALE_AUTH_KEY to TAILSCALE_AUTHKEY
        TAILSCALE_AUTH_KEY=$(grep "^TAILSCALE_AUTH_KEY=" .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
        export TAILSCALE_AUTHKEY="$TAILSCALE_AUTH_KEY"
        echo "   Found TAILSCALE_AUTH_KEY, using as TAILSCALE_AUTHKEY"
    fi
fi

# Create Tailscale state directory if it doesn't exist
mkdir -p /var/lib/tailscale
mkdir -p /var/run/tailscale

# Start Tailscale daemon in the background
if [ -n "$TAILSCALE_AUTHKEY" ]; then
    echo "🔐 Starting Tailscale..."
    
    # Start tailscaled
    tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock &
    TAILSCALED_PID=$!
    
    # Wait for tailscaled to be ready
    sleep 3
    
    # Authenticate Tailscale (non-blocking - don't wait for approval)
    echo "🔑 Authenticating Tailscale..."
    tailscale up \
        --authkey="$TAILSCALE_AUTHKEY" \
        --hostname="${FLY_APP_NAME:-bop-wispy-voice-3017}" \
        --accept-routes \
        --accept-dns=false \
        --advertise-exit-node=false &
    TAILSCALE_UP_PID=$!
    
    # Wait a moment for Tailscale to start connecting
    sleep 2
    
    # Get and display Tailscale IP (may not be available yet if not approved)
    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "not available")
    if [ "$TAILSCALE_IP" != "not available" ]; then
        echo "✅ Tailscale connected! IP: $TAILSCALE_IP"
        echo "📱 Access from Tailscale devices: http://$TAILSCALE_IP:${PORT:-8080}"
    else
        echo "⏳ Tailscale connecting (waiting for approval)..."
        echo "💡 Approve at: https://login.tailscale.com/admin/machines"
    fi
else
    echo "⚠️  TAILSCALE_AUTHKEY not set, skipping Tailscale setup"
    echo "💡 Set it with: flyctl secrets set TAILSCALE_AUTHKEY=tskey-... -a bop-wispy-voice-3017"
fi

# Start the BOP server
echo "🌐 Starting BOP web server on port ${PORT:-8080}..."
echo "📦 Python path: $PYTHONPATH"
echo "📦 Working directory: $(pwd)"
echo "📦 Checking if bop.server module exists..."
python3 -c "import sys; sys.path.insert(0, '/app/src'); from bop.server import app; print('✅ Server module loads successfully')" || echo "⚠️  Server module check failed"
echo "🚀 Launching Uvicorn..."
exec uv run python -m uvicorn bop.server:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info

