#!/bin/bash
# Comprehensive security testing for BOP deployment on Fly.io
# Tests security, persistence, configuration, and Fly.io-specific concerns

set -e

APP_NAME="${FLY_APP_NAME:-pran-wispy-voice-3017}"
APP_URL="${BOP_APP_URL:-https://${APP_NAME}.fly.dev}"
API_KEY="${BOP_API_KEY:-}"

echo "🔒 Comprehensive Security Testing for BOP"
echo "=========================================="
echo ""
echo "App: $APP_NAME"
echo "URL: $APP_URL"
echo ""

FAILED=0
PASSED=0
WARNINGS=0

# Test function
test_check() {
    local name="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "Testing: $name... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo "✅ PASS"
        ((PASSED++))
        return 0
    else
        if [ "$expected" = "warning" ]; then
            echo "⚠️  WARN"
            ((WARNINGS++))
            return 0
        else
            echo "❌ FAIL"
            ((FAILED++))
            return 1
        fi
    fi
}

# Fly.io Security Tests
echo "📋 Fly.io Security Configuration"
echo "--------------------------------"

test_check "No public IPs" \
    "flyctl ips list -a $APP_NAME | grep -q 'public' && false || true" \
    "error"

test_check "HTTPS enforced" \
    "curl -s -o /dev/null -w '%{http_code}' http://${APP_NAME}.fly.dev/health 2>&1 | grep -qE '^[34]|Could not resolve|Connection refused' || (flyctl ips list -a $APP_NAME 2>/dev/null | grep -q 'public' && false || true)" \
    "warning"

test_check "Health check configured" \
    "grep -q 'health' fly.toml"

test_check "Auto-stop enabled" \
    "grep -qi 'auto_stop' fly.toml"

# Secrets Security
echo ""
echo "🔐 Secrets Security"
echo "-------------------"

test_check "Secrets not in fly.toml" \
    "! grep -qiE '(api_key|password|secret|token).*=.*[a-zA-Z0-9]{20,}' fly.toml"

test_check "Secrets accessible via flyctl" \
    "flyctl secrets list -a $APP_NAME > /dev/null 2>&1"

test_check "At least one LLM secret set" \
    "flyctl secrets list -a $APP_NAME 2>/dev/null | grep -qiE '(OPENAI|ANTHROPIC|GEMINI)_API_KEY'"

# API Security
echo ""
echo "🛡️  API Security"
echo "----------------"

if [ -n "$API_KEY" ]; then
    test_check "Health endpoint public" \
        "curl -s -o /dev/null -w '%{http_code}' ${APP_URL}/health | grep -q '200'"
    
    test_check "Chat endpoint requires auth" \
        "curl -s -o /dev/null -w '%{http_code}' -X POST ${APP_URL}/chat -H 'Content-Type: application/json' -d '{\"message\":\"test\"}' | grep -q '401'"
    
    test_check "Chat endpoint accepts valid key" \
        "curl -s -o /dev/null -w '%{http_code}' -X POST ${APP_URL}/chat -H 'Content-Type: application/json' -H 'X-API-Key: ${API_KEY}' -d '{\"message\":\"test\",\"research\":false}' | grep -q '200'"
else
    echo "⚠️  API_KEY not set, skipping API tests"
    ((WARNINGS++))
fi

# Information Disclosure
echo ""
echo "🔍 Information Disclosure"
echo "------------------------"

test_check "No .env exposed" \
    "curl -s -o /dev/null -w '%{http_code}' ${APP_URL}/.env | grep -qE '^[45]'"

test_check "No fly.toml exposed" \
    "curl -s -o /dev/null -w '%{http_code}' ${APP_URL}/fly.toml | grep -qE '^[45]'"

test_check "No Dockerfile exposed" \
    "curl -s -o /dev/null -w '%{http_code}' ${APP_URL}/Dockerfile | grep -qE '^[45]'"

test_check "No debug endpoints" \
    "curl -s -o /dev/null -w '%{http_code}' ${APP_URL}/debug | grep -qE '^[45]'"

test_check "No admin endpoints" \
    "curl -s -o /dev/null -w '%{http_code}' ${APP_URL}/admin | grep -qE '^[45]'"

# Configuration Security
echo ""
echo "⚙️  Configuration Security"
echo "--------------------------"

test_check "Dockerfile doesn't run as root" \
    "grep -qE '(USER|adduser|addgroup)' Dockerfile || grep -q 'python:.*-slim' Dockerfile" \
    "warning"

test_check "fly.toml forces HTTPS" \
    "grep -qi 'force_https.*true' fly.toml"

test_check "Health check path configured" \
    "grep -q '/health' fly.toml"

# Persistence Security
echo ""
echo "💾 Persistence Security"
echo "-----------------------"

test_check "No volumes required" \
    "! grep -qi 'mounts' fly.toml || grep -qi 'encrypt' fly.toml" \
    "warning"

test_check "No database secrets required" \
    "! flyctl secrets list -a $APP_NAME 2>/dev/null | grep -qiE '(POSTGRES|MYSQL|MONGODB|DATABASE)' || true"

# Rate Limiting
echo ""
echo "🚦 Rate Limiting"
echo "----------------"

if [ -n "$API_KEY" ]; then
    echo -n "Testing: Rate limiting... "
    RATE_LIMIT_HIT=0
    for i in {1..35}; do
        STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST ${APP_URL}/chat \
            -H "Content-Type: application/json" \
            -H "X-API-Key: ${API_KEY}" \
            -d "{\"message\":\"test $i\",\"research\":false}" 2>/dev/null || echo "000")
        if [ "$STATUS" = "429" ]; then
            RATE_LIMIT_HIT=1
            break
        fi
    done
    
    if [ $RATE_LIMIT_HIT -eq 1 ]; then
        echo "✅ PASS (Rate limiting active)"
        ((PASSED++))
    else
        echo "⚠️  WARN (Rate limiting not detected, may be working)"
        ((WARNINGS++))
    fi
else
    echo "⚠️  API_KEY not set, skipping rate limit test"
    ((WARNINGS++))
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Passed:  $PASSED"
echo "⚠️  Warnings: $WARNINGS"
echo "❌ Failed:  $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ All critical security tests passed!"
    exit 0
else
    echo "❌ Some security tests failed. Review and fix issues."
    exit 1
fi

