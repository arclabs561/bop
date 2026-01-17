#!/bin/bash
# Verify deployment after deployment completes
# Checks health, API endpoints, and basic functionality

set -e

APP_NAME="${FLY_APP_NAME:-pran-wispy-voice-3017}"
APP_URL="https://${APP_NAME}.fly.dev"
MAX_RETRIES=30
RETRY_DELAY=2

echo "🔍 Verifying deployment for $APP_NAME..."

# Check if flyctl is available
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl not found. Install with: curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Wait for app to be ready
echo "⏳ Waiting for app to be ready..."
for i in $(seq 1 $MAX_RETRIES); do
    if flyctl status -a "$APP_NAME" &> /dev/null; then
        STATUS=$(flyctl status -a "$APP_NAME" 2>/dev/null | grep -i "status" | head -1 || echo "")
        if echo "$STATUS" | grep -qi "started\|running"; then
            echo "✅ App is running"
            break
        fi
    fi
    
    if [ $i -eq $MAX_RETRIES ]; then
        echo "❌ App did not become ready after $((MAX_RETRIES * RETRY_DELAY)) seconds"
        echo "   Check status: flyctl status -a $APP_NAME"
        echo "   Check logs: flyctl logs -a $APP_NAME --no-tail"
        exit 1
    fi
    
    echo "   Attempt $i/$MAX_RETRIES: Waiting ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
done

# Test health endpoint
echo ""
echo "🏥 Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$APP_URL/health" || echo -e "\n000")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health check passed (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
else
    echo "❌ Health check failed (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
    exit 1
fi

# Test root endpoint
echo ""
echo "🌐 Testing root endpoint..."
ROOT_RESPONSE=$(curl -s -w "\n%{http_code}" "$APP_URL/" || echo -e "\n000")
ROOT_CODE=$(echo "$ROOT_RESPONSE" | tail -1)

if [ "$ROOT_CODE" = "200" ]; then
    echo "✅ Root endpoint accessible (HTTP $ROOT_CODE)"
else
    echo "⚠️  Root endpoint returned HTTP $ROOT_CODE (may be expected)"
fi

# Check if API key is required
echo ""
echo "🔐 Checking API key requirement..."
API_KEY=$(flyctl secrets list -a "$APP_NAME" 2>/dev/null | grep "BOP_API_KEY" | awk '{print $2}' || echo "")

if [ -n "$API_KEY" ]; then
    echo "✅ API key is set (BOP_API_KEY secret exists)"
    echo "   Testing protected endpoint with API key..."
    
    CHAT_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$APP_URL/chat" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d '{"message": "test", "research": false}' || echo -e "\n000")
    
    CHAT_CODE=$(echo "$CHAT_RESPONSE" | tail -1)
    
    if [ "$CHAT_CODE" = "200" ]; then
        echo "✅ Protected endpoint accessible with API key (HTTP $CHAT_CODE)"
    elif [ "$CHAT_CODE" = "401" ]; then
        echo "⚠️  API key authentication failed (HTTP $CHAT_CODE)"
        echo "   This may indicate the API key secret doesn't match"
    else
        echo "⚠️  Protected endpoint returned HTTP $CHAT_CODE"
    fi
else
    echo "⚠️  No API key set (BOP_API_KEY secret not found)"
    echo "   Protected endpoints may be accessible without authentication"
fi

# Check constraint solver status
echo ""
echo "🧮 Checking constraint solver..."
CONSTRAINTS_RESPONSE=$(curl -s -w "\n%{http_code}" "$APP_URL/constraints/status" 2>/dev/null || echo -e "\n000")
CONSTRAINTS_CODE=$(echo "$CONSTRAINTS_RESPONSE" | tail -1)

if [ "$CONSTRAINTS_CODE" = "200" ] || [ "$CONSTRAINTS_CODE" = "401" ]; then
    if [ "$CONSTRAINTS_CODE" = "200" ]; then
        CONSTRAINTS_BODY=$(echo "$CONSTRAINTS_RESPONSE" | head -n -1)
        echo "✅ Constraint solver endpoint accessible"
        echo "   Response: $CONSTRAINTS_BODY"
    else
        echo "✅ Constraint solver endpoint requires authentication (expected)"
    fi
else
    echo "⚠️  Constraint solver endpoint returned HTTP $CONSTRAINTS_CODE"
fi

# Check public IPs
echo ""
echo "🌍 Checking public IPs..."
IPS=$(flyctl ips list -a "$APP_NAME" 2>/dev/null || echo "")
PUBLIC_IPS=$(echo "$IPS" | grep -v "private" | grep -v "PRIVATE" | grep -E "v4|v6" | wc -l | tr -d ' ')

if [ "$PUBLIC_IPS" -eq 0 ]; then
    echo "✅ No public IPs (private deployment)"
else
    echo "⚠️  $PUBLIC_IPS public IP(s) found"
    echo "   Consider removing for private deployment: ./scripts/make_private.sh"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Deployment verification complete!"
echo ""
echo "📊 Summary:"
echo "   App: $APP_NAME"
echo "   URL: $APP_URL"
echo "   Health: ✅"
echo "   Status: $(flyctl status -a "$APP_NAME" 2>/dev/null | grep -i "status" | head -1 | awk '{print $2}' || echo "unknown")"
echo ""
echo "🔗 Quick links:"
echo "   Status: flyctl status -a $APP_NAME"
echo "   Logs: flyctl logs -a $APP_NAME --no-tail"
echo "   Dashboard: flyctl dashboard -a $APP_NAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

