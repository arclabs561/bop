#!/bin/bash
# Red team security tests - rerunnable security validation

set -e

APP_URL="${BOP_APP_URL:-https://bop-wispy-voice-3017.fly.dev}"
API_KEY="${BOP_API_KEY:-a03zsJxmWd5rZeIHDN20ZjkM_qbmfKCIEf-bP8ABTdc}"

echo "🔴 Red Team Security Tests"
echo "=========================="
echo "App URL: $APP_URL"
echo ""

PASSED=0
FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo "✅ $2"
        ((PASSED++))
    else
        echo "❌ $2"
        ((FAILED++))
    fi
}

# Test 1: Health endpoint accessible without auth
echo "Test 1: Health endpoint (no auth required)"
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL/health" || echo "000")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    test_result 0 "Health endpoint accessible"
else
    test_result 1 "Health endpoint failed (got $HEALTH_RESPONSE)"
fi

# Test 2: Chat endpoint requires auth
echo ""
echo "Test 2: Chat endpoint authentication"
CHAT_NO_AUTH=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -d '{"message":"test"}' 2>/dev/null || echo "000")
if [ "$CHAT_NO_AUTH" = "401" ]; then
    test_result 0 "Chat endpoint requires authentication"
else
    test_result 1 "Chat endpoint auth check failed (got $CHAT_NO_AUTH)"
fi

# Test 3: Invalid API key rejected
echo ""
echo "Test 3: Invalid API key rejection"
CHAT_INVALID=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: invalid-key-12345" \
    -d '{"message":"test"}' 2>/dev/null || echo "000")
if [ "$CHAT_INVALID" = "401" ]; then
    test_result 0 "Invalid API key rejected"
else
    test_result 1 "Invalid API key check failed (got $CHAT_INVALID)"
fi

# Test 4: Valid API key accepted
echo ""
echo "Test 4: Valid API key acceptance"
CHAT_VALID=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"message":"test","research":false}' --max-time 30 || echo "000")
if [ "$CHAT_VALID" = "200" ]; then
    test_result 0 "Valid API key accepted"
else
    test_result 1 "Valid API key check failed (got $CHAT_VALID)"
fi

# Test 5: Metrics endpoint requires auth
echo ""
echo "Test 5: Metrics endpoint authentication"
METRICS_NO_AUTH=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL/metrics" || echo "000")
if [ "$METRICS_NO_AUTH" = "401" ]; then
    test_result 0 "Metrics endpoint requires authentication"
else
    test_result 1 "Metrics endpoint auth check failed (got $METRICS_NO_AUTH)"
fi

# Test 6: SQL injection attempt
echo ""
echo "Test 6: SQL injection protection"
SQL_INJECT=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"message":"test'\''; DROP TABLE users; --","research":false}' --max-time 30 || echo "000")
if [ "$SQL_INJECT" != "500" ]; then
    test_result 0 "SQL injection handled safely"
else
    test_result 1 "SQL injection caused server error"
fi

# Test 7: XSS attempt
echo ""
echo "Test 7: XSS protection"
XSS_RESPONSE=$(curl -s -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"message":"<script>alert(1)</script>","research":false}' --max-time 30 || echo "")
XSS_STATUS=$(echo "$XSS_RESPONSE" | head -1 | grep -o "[0-9]\{3\}" || echo "000")
if [ "$XSS_STATUS" != "500" ] && [ -n "$XSS_RESPONSE" ]; then
    # Check response doesn't contain script tag
    if echo "$XSS_RESPONSE" | grep -qi "<script>" > /dev/null 2>&1; then
        test_result 1 "XSS script tag in response"
    else
        test_result 0 "XSS handled safely"
    fi
else
    test_result 1 "XSS test failed"
fi

# Test 8: Oversized payload
echo ""
echo "Test 8: Oversized payload handling"
LARGE_MSG=$(python3 -c "print('x' * 10000)")
LARGE_PAYLOAD=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "{\"message\":\"$LARGE_MSG\",\"research\":false}" --max-time 30 || echo "000")
if [ "$LARGE_PAYLOAD" != "500" ]; then
    test_result 0 "Oversized payload handled"
else
    test_result 1 "Oversized payload caused server error"
fi

# Test 9: Malformed JSON
echo ""
echo "Test 9: Malformed JSON handling"
MALFORMED=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "not json" || echo "000")
if [ "$MALFORMED" = "400" ] || [ "$MALFORMED" = "422" ]; then
    test_result 0 "Malformed JSON rejected"
else
    test_result 1 "Malformed JSON check failed (got $MALFORMED)"
fi

# Test 10: Error message security
echo ""
echo "Test 10: Error message security"
ERROR_RESPONSE=$(curl -s "$APP_URL/nonexistent" || echo "")
if echo "$ERROR_RESPONSE" | grep -qi "/app/\|/usr/\|/var/" > /dev/null 2>&1; then
    test_result 1 "Error messages leak file paths"
else
    test_result 0 "Error messages don't leak paths"
fi

# Test 11: HTTPS enforcement
echo ""
echo "Test 11: HTTPS enforcement"
HTTP_URL=$(echo "$APP_URL" | sed 's|https://|http://|')
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$HTTP_URL/health" --max-time 5 2>&1 || echo "000")
if [ "$HTTP_RESPONSE" = "301" ] || [ "$HTTP_RESPONSE" = "302" ] || [ "$HTTP_RESPONSE" = "308" ]; then
    test_result 0 "HTTP redirects to HTTPS"
elif echo "$HTTP_RESPONSE" | grep -qi "ssl\|tls" > /dev/null 2>&1; then
    test_result 0 "HTTPS enforced"
else
    test_result 1 "HTTPS enforcement check (got $HTTP_RESPONSE)"
fi

# Test 12: Server header security
echo ""
echo "Test 12: Server header security"
SERVER_HEADER=$(curl -s -I "$APP_URL/health" | grep -i "server:" | tr -d '\r\n' || echo "")
if echo "$SERVER_HEADER" | grep -qi "uvicorn\|python" > /dev/null 2>&1; then
    test_result 1 "Server header exposes version info"
else
    test_result 0 "Server header doesn't expose version"
fi

# Test 13: Debug endpoints
echo ""
echo "Test 13: Debug endpoint security"
DEBUG_PATHS=("/debug" "/admin" "/.env" "/config")
DEBUG_FAILED=0
for path in "${DEBUG_PATHS[@]}"; do
    DEBUG_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL$path" --max-time 5 || echo "000")
    if [ "$DEBUG_RESPONSE" = "200" ]; then
        DEBUG_FAILED=1
        break
    fi
done
if [ $DEBUG_FAILED -eq 0 ]; then
    test_result 0 "Debug endpoints not exposed"
else
    test_result 1 "Debug endpoints accessible"
fi

# Summary
echo ""
echo "=========================="
echo "Test Summary"
echo "=========================="
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo "Total: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All security tests passed!"
    exit 0
else
    echo "⚠️  Some security tests failed. Review above."
    exit 1
fi

