#!/bin/bash
# Test BOP locally with Tailscale

set -e

echo "🧪 Testing BOP locally..."

# Load .env
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
    echo "❌ TAILSCALE_AUTHKEY not set in .env"
    echo "   Add to .env: TAILSCALE_AUTHKEY=tskey-... (or TAILSCALE_AUTH_KEY=tskey-...)"
    exit 1
fi

echo "✅ TAILSCALE_AUTHKEY found"

# Start server in background
echo ""
echo "🚀 Starting BOP server..."
uv run python -m uvicorn bop.server:app --host 0.0.0.0 --port 8080 &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Test health endpoint
echo ""
echo "🔍 Testing health endpoint..."
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ Health check passed"
    curl -s http://localhost:8080/health | jq . || curl -s http://localhost:8080/health
else
    echo "❌ Health check failed"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Test web UI
echo ""
echo "🔍 Testing web UI..."
if curl -s http://localhost:8080/ | grep -q "BOP"; then
    echo "✅ Web UI accessible"
else
    echo "⚠️  Web UI may not be loading correctly"
fi

# Test chat endpoint (if API key not required)
echo ""
echo "🔍 Testing chat endpoint..."
CHAT_RESPONSE=$(curl -s -X POST http://localhost:8080/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "test", "research": false}' 2>&1)

if echo "$CHAT_RESPONSE" | grep -q "response\|error"; then
    echo "✅ Chat endpoint responding"
    echo "$CHAT_RESPONSE" | jq . || echo "$CHAT_RESPONSE"
else
    echo "⚠️  Chat endpoint may require API key"
    echo "$CHAT_RESPONSE"
fi

# Cleanup
echo ""
echo "🛑 Stopping server..."
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo ""
echo "✅ Local test complete!"

