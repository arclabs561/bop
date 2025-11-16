#!/bin/bash
# Test Tailscale connection and access

set -e

echo "🧪 Testing Tailscale setup..."

# Load .env if it exists
if [ -f .env ]; then
    echo "📄 Loading .env file..."
    # Try both TAILSCALE_AUTHKEY and TAILSCALE_AUTH_KEY
    if grep -q "^TAILSCALE_AUTHKEY=" .env; then
        export $(grep -v '^#' .env | grep -v '^$' | grep "^TAILSCALE_AUTHKEY=" | xargs)
    elif grep -q "^TAILSCALE_AUTH_KEY=" .env; then
        TAILSCALE_AUTH_KEY=$(grep "^TAILSCALE_AUTH_KEY=" .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
        export TAILSCALE_AUTHKEY="$TAILSCALE_AUTH_KEY"
        echo "   Found TAILSCALE_AUTH_KEY, using as TAILSCALE_AUTHKEY"
    fi
fi

# Check if Tailscale auth key is set
if [ -z "$TAILSCALE_AUTHKEY" ]; then
    echo "❌ TAILSCALE_AUTHKEY not set in environment or .env"
    echo "   Set it in .env: TAILSCALE_AUTHKEY=tskey-... (or TAILSCALE_AUTH_KEY=tskey-...)"
    exit 1
fi

echo "✅ TAILSCALE_AUTHKEY found"

# Test local Tailscale connection (if tailscale CLI is available)
if command -v tailscale &> /dev/null; then
    echo ""
    echo "🔍 Checking local Tailscale status..."
    if tailscale status &> /dev/null; then
        echo "✅ Tailscale is running locally"
        tailscale status | head -5
    else
        echo "⚠️  Tailscale not running locally (this is OK for Fly.io deployment)"
    fi
else
    echo "⚠️  Tailscale CLI not installed locally (this is OK for Fly.io deployment)"
fi

# Test Fly.io app (if deployed)
APP_NAME="bop-wispy-voice-3017"
if flyctl apps list 2>/dev/null | grep -q "$APP_NAME"; then
    echo ""
    echo "🔍 Checking Fly.io app status..."
    echo "   App: $APP_NAME"
    
    # Check if Tailscale is connected
    echo ""
    echo "📋 Checking Tailscale connection in Fly.io logs..."
    flyctl logs -a "$APP_NAME" 2>/dev/null | tail -50 | grep -i tailscale || echo "   (No Tailscale logs found - may need to deploy)"
    
    # Check IPs
    echo ""
    echo "📋 Current IP addresses:"
    flyctl ips list -a "$APP_NAME"
    
    # Check if public IPs exist
    PUBLIC_IPS=$(flyctl ips list -a "$APP_NAME" | grep -v "private" | grep -v "IPv6" | wc -l)
    if [ "$PUBLIC_IPS" -gt 1 ]; then
        echo ""
        echo "⚠️  Public IPs detected. Run: ./scripts/make_private.sh"
    else
        echo ""
        echo "✅ App appears to be private (no public IPs)"
    fi
else
    echo ""
    echo "⚠️  App $APP_NAME not found or not logged into Fly.io"
    echo "   Run: flyctl auth login"
fi

echo ""
echo "✅ Test complete!"

