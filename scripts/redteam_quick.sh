#!/bin/bash
# Quick red team security validation (fast, non-blocking)

APP_URL="${BOP_APP_URL:-https://pran-wispy-voice-3017.fly.dev}"
API_KEY="${BOP_API_KEY:-a03zsJxmWd5rZeIHDN20ZjkM_qbmfKCIEf-bP8ABTdc}"

echo "🔴 Quick Security Check"
echo "======================"

# Quick health check
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$APP_URL/health" 2>/dev/null || echo "000")
if [ "$HEALTH" = "200" ]; then
    echo "✅ Health endpoint: OK"
else
    echo "❌ Health endpoint: FAIL ($HEALTH)"
fi

# Quick auth check
AUTH=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" -d '{"message":"test"}' 2>/dev/null || echo "000")
if [ "$AUTH" = "401" ]; then
    echo "✅ Authentication: OK"
else
    echo "❌ Authentication: FAIL ($AUTH)"
fi

# Quick valid key check
VALID=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"message":"test","research":false}' 2>/dev/null || echo "000")
if [ "$VALID" = "200" ]; then
    echo "✅ Valid API key: OK"
else
    echo "⚠️  Valid API key: $VALID (may be slow)"
fi

echo "======================"
echo "Quick check complete"

