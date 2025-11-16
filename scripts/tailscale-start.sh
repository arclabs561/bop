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
    
    # Authenticate Tailscale
    echo "🔑 Authenticating Tailscale..."
    tailscale up \
        --authkey="$TAILSCALE_AUTHKEY" \
        --hostname="${FLY_APP_NAME:-bop-wispy-voice-3017}" \
        --accept-routes \
        --accept-dns=false \
        --advertise-exit-node=false
    
    # Get and display Tailscale IP
    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "not available")
    echo "✅ Tailscale connected! IP: $TAILSCALE_IP"
    echo "📱 Access from Tailscale devices: http://$TAILSCALE_IP:${PORT:-8080}"
else
    echo "⚠️  TAILSCALE_AUTHKEY not set, skipping Tailscale setup"
    echo "💡 Set it with: flyctl secrets set TAILSCALE_AUTHKEY=tskey-... -a bop-wispy-voice-3017"
fi

# Start the BOP server
echo "🌐 Starting BOP web server on port ${PORT:-8080}..."
exec uv run python -m uvicorn bop.server:app --host 0.0.0.0 --port ${PORT:-8080}

