#!/bin/bash
# Test deployed BOP service via Tailscale

set -e

APP_NAME="bop-wispy-voice-3017"

echo "🧪 Testing deployed BOP service..."

# Get Tailscale IP from Fly.io
echo "🔍 Getting Tailscale IP from Fly.io..."
TAILSCALE_IP=$(flyctl ssh console -a "$APP_NAME" -C "tailscale ip -4" 2>/dev/null | grep -E "^100\." | head -1)

if [ -z "$TAILSCALE_IP" ]; then
    echo "❌ Could not get Tailscale IP"
    echo "   Check if Tailscale is connected: flyctl logs -a $APP_NAME | grep Tailscale"
    exit 1
fi

echo "✅ Tailscale IP: $TAILSCALE_IP"

# Test health endpoint
echo ""
echo "🔍 Testing health endpoint..."
if curl -s "http://$TAILSCALE_IP:8080/health" > /dev/null; then
    echo "✅ Health check passed"
    curl -s "http://$TAILSCALE_IP:8080/health" | jq . || curl -s "http://$TAILSCALE_IP:8080/health"
else
    echo "❌ Health check failed"
    echo "   Make sure you're connected to Tailscale: tailscale status"
    exit 1
fi

# Test web UI
echo ""
echo "🔍 Testing web UI..."
if curl -s "http://$TAILSCALE_IP:8080/" | grep -q "BOP"; then
    echo "✅ Web UI accessible"
    echo "   Open in browser: http://$TAILSCALE_IP:8080"
else
    echo "⚠️  Web UI may not be loading correctly"
fi

# Test chat endpoint
echo ""
echo "🔍 Testing chat endpoint..."
CHAT_RESPONSE=$(curl -s -X POST "http://$TAILSCALE_IP:8080/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "test", "research": false}' 2>&1)

if echo "$CHAT_RESPONSE" | grep -q "response\|error"; then
    echo "✅ Chat endpoint responding"
    echo "$CHAT_RESPONSE" | jq . || echo "$CHAT_RESPONSE"
else
    echo "⚠️  Chat endpoint may require API key"
    echo "$CHAT_RESPONSE"
fi

echo ""
echo "✅ Deployment test complete!"
echo ""
echo "📱 Access from mobile:"
echo "   http://$TAILSCALE_IP:8080"

