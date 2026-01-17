#!/bin/bash
# Comprehensive red team security tests with detailed reporting

set -e

APP_URL="${BOP_APP_URL:-https://pran-wispy-voice-3017.fly.dev}"
API_KEY="${BOP_API_KEY:-a03zsJxmWd5rZeIHDN20ZjkM_qbmfKCIEf-bP8ABTdc}"

REPORT_FILE="redteam_report_$(date +%Y%m%d_%H%M%S).txt"

echo "🔴 Comprehensive Red Team Security Assessment" | tee "$REPORT_FILE"
echo "=============================================" | tee -a "$REPORT_FILE"
echo "Target: $APP_URL" | tee -a "$REPORT_FILE"
echo "Date: $(date)" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

PASSED=0
FAILED=0
WARNINGS=0

test_result() {
    local status=$1
    local test_name=$2
    local details=$3
    
    if [ $status -eq 0 ]; then
        echo "✅ PASS: $test_name" | tee -a "$REPORT_FILE"
        [ -n "$details" ] && echo "   $details" | tee -a "$REPORT_FILE"
        ((PASSED++))
    elif [ $status -eq 2 ]; then
        echo "⚠️  WARN: $test_name" | tee -a "$REPORT_FILE"
        [ -n "$details" ] && echo "   $details" | tee -a "$REPORT_FILE"
        ((WARNINGS++))
    else
        echo "❌ FAIL: $test_name" | tee -a "$REPORT_FILE"
        [ -n "$details" ] && echo "   $details" | tee -a "$REPORT_FILE"
        ((FAILED++))
    fi
}

# Authentication Tests
echo "🔐 Authentication Tests" | tee -a "$REPORT_FILE"
echo "----------------------" | tee -a "$REPORT_FILE"

# Test: Health endpoint
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL/health" 2>/dev/null || echo "000")
test_result $([ "$HEALTH" = "200" ] && echo 0 || echo 1) \
    "Health endpoint accessible" \
    "Status: $HEALTH"

# Test: Chat without auth
CHAT_NO_AUTH=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" -d '{"message":"test"}' 2>/dev/null || echo "000")
test_result $([ "$CHAT_NO_AUTH" = "401" ] && echo 0 || echo 1) \
    "Chat endpoint requires authentication" \
    "Status: $CHAT_NO_AUTH (expected 401)"

# Test: Invalid API key
INVALID_KEY=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: invalid-key" \
    -d '{"message":"test"}' 2>/dev/null || echo "000")
test_result $([ "$INVALID_KEY" = "401" ] && echo 0 || echo 1) \
    "Invalid API key rejected" \
    "Status: $INVALID_KEY (expected 401)"

# Test: Valid API key
VALID_KEY=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"message":"test","research":false}' --max-time 30 2>/dev/null || echo "000")
test_result $([ "$VALID_KEY" = "200" ] && echo 0 || echo 1) \
    "Valid API key accepted" \
    "Status: $VALID_KEY (expected 200)"

# Test: Metrics endpoint
METRICS=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL/metrics" 2>/dev/null || echo "000")
test_result $([ "$METRICS" = "401" ] && echo 0 || echo 1) \
    "Metrics endpoint requires authentication" \
    "Status: $METRICS (expected 401)"

echo "" | tee -a "$REPORT_FILE"

# Input Validation Tests
echo "🛡️  Input Validation Tests" | tee -a "$REPORT_FILE"
echo "------------------------" | tee -a "$REPORT_FILE"

# SQL Injection
SQL_TEST=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"message":"test'\''; DROP TABLE users; --","research":false}' --max-time 30 2>/dev/null || echo "000")
test_result $([ "$SQL_TEST" != "500" ] && echo 0 || echo 1) \
    "SQL injection protection" \
    "Status: $SQL_TEST (should not be 500)"

# XSS
XSS_RESPONSE=$(curl -s -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"message":"<script>alert(1)</script>","research":false}' --max-time 30 2>/dev/null || echo "")
XSS_STATUS=$(echo "$XSS_RESPONSE" | head -1 | grep -o "[0-9]\{3\}" || echo "000")
XSS_HAS_SCRIPT=$(echo "$XSS_RESPONSE" | grep -qi "<script>" && echo "yes" || echo "no")
test_result $([ "$XSS_STATUS" != "500" ] && [ "$XSS_HAS_SCRIPT" = "no" ] && echo 0 || echo 1) \
    "XSS protection" \
    "Status: $XSS_STATUS, Contains script: $XSS_HAS_SCRIPT"

# Command Injection
CMD_TEST=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"message":"test; rm -rf /","research":false}' --max-time 30 2>/dev/null || echo "000")
test_result $([ "$CMD_TEST" != "500" ] && echo 0 || echo 1) \
    "Command injection protection" \
    "Status: $CMD_TEST (should not be 500)"

# Oversized payload
LARGE_MSG=$(python3 -c "print('x' * 50000)" 2>/dev/null || echo "x"*1000)
LARGE_TEST=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "{\"message\":\"$LARGE_MSG\",\"research\":false}" --max-time 30 2>/dev/null || echo "000")
test_result $([ "$LARGE_TEST" != "500" ] && echo 0 || echo 1) \
    "Oversized payload handling" \
    "Status: $LARGE_TEST (should not be 500)"

# Malformed JSON
MALFORMED=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/chat" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "not json" 2>/dev/null || echo "000")
test_result $([ "$MALFORMED" = "400" ] || [ "$MALFORMED" = "422" ] && echo 0 || echo 1) \
    "Malformed JSON rejection" \
    "Status: $MALFORMED (expected 400 or 422)"

echo "" | tee -a "$REPORT_FILE"

# Information Disclosure Tests
echo "🔍 Information Disclosure Tests" | tee -a "$REPORT_FILE"
echo "-------------------------------" | tee -a "$REPORT_FILE"

# Error messages
ERROR_RESPONSE=$(curl -s "$APP_URL/nonexistent" 2>/dev/null || echo "")
ERROR_LEAKS=$(echo "$ERROR_RESPONSE" | grep -qi "/app/\|/usr/\|/var/" && echo "yes" || echo "no")
test_result $([ "$ERROR_LEAKS" = "no" ] && echo 0 || echo 1) \
    "Error messages don't leak paths" \
    "Leaks paths: $ERROR_LEAKS"

# Server header
SERVER_HEADER=$(curl -s -I "$APP_URL/health" 2>/dev/null | grep -i "server:" | tr -d '\r\n' || echo "")
SERVER_EXPOSES=$(echo "$SERVER_HEADER" | grep -qi "uvicorn\|python" && echo "yes" || echo "no")
test_result $([ "$SERVER_EXPOSES" = "no" ] && echo 0 || echo 1) \
    "Server header security" \
    "Exposes version: $SERVER_EXPOSES"

# Debug endpoints
DEBUG_PATHS=("/debug" "/admin" "/.env" "/config" "/secrets")
DEBUG_EXPOSED=0
for path in "${DEBUG_PATHS[@]}"; do
    DEBUG_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL$path" --max-time 5 2>/dev/null || echo "000")
    if [ "$DEBUG_CODE" = "200" ]; then
        DEBUG_EXPOSED=1
        break
    fi
done
test_result $([ $DEBUG_EXPOSED -eq 0 ] && echo 0 || echo 1) \
    "Debug endpoints not exposed" \
    "Exposed: $([ $DEBUG_EXPOSED -eq 1 ] && echo "yes" || echo "no")"

echo "" | tee -a "$REPORT_FILE"

# TLS/HTTPS Tests
echo "🔒 TLS/HTTPS Tests" | tee -a "$REPORT_FILE"
echo "-----------------" | tee -a "$REPORT_FILE"

HTTP_URL=$(echo "$APP_URL" | sed 's|https://|http://|')
HTTP_TEST=$(curl -s -o /dev/null -w "%{http_code}" "$HTTP_URL/health" --max-time 5 2>&1 || echo "000")
HTTPS_ENFORCED=$([ "$HTTP_TEST" = "301" ] || [ "$HTTP_TEST" = "302" ] || [ "$HTTP_TEST" = "308" ] && echo "yes" || echo "no")
test_result $([ "$HTTPS_ENFORCED" = "yes" ] && echo 0 || echo 2) \
    "HTTPS enforcement" \
    "Redirects HTTP to HTTPS: $HTTPS_ENFORCED"

# TLS version (basic check - successful HTTPS connection implies TLS 1.2+)
HTTPS_WORKS=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL/health" 2>/dev/null || echo "000")
test_result $([ "$HTTPS_WORKS" = "200" ] && echo 0 || echo 1) \
    "TLS connection successful" \
    "HTTPS status: $HTTPS_WORKS"

echo "" | tee -a "$REPORT_FILE"

# Rate Limiting Tests
echo "⚡ Rate Limiting Tests" | tee -a "$REPORT_FILE"
echo "---------------------" | tee -a "$REPORT_FILE"

RAPID_COUNT=0
for i in {1..20}; do
    RAPID_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/chat" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d '{"message":"test","research":false}' --max-time 5 2>/dev/null || echo "000")
    if [ "$RAPID_RESPONSE" = "200" ] || [ "$RAPID_RESPONSE" = "429" ]; then
        ((RAPID_COUNT++))
    fi
done
test_result $([ $RAPID_COUNT -gt 0 ] && echo 0 || echo 1) \
    "Rapid requests handling" \
    "Successful/rate-limited: $RAPID_COUNT/20"

echo "" | tee -a "$REPORT_FILE"

# Summary
echo "==============================" | tee -a "$REPORT_FILE"
echo "Test Summary" | tee -a "$REPORT_FILE"
echo "==============================" | tee -a "$REPORT_FILE"
echo "✅ Passed: $PASSED" | tee -a "$REPORT_FILE"
echo "⚠️  Warnings: $WARNINGS" | tee -a "$REPORT_FILE"
echo "❌ Failed: $FAILED" | tee -a "$REPORT_FILE"
echo "Total: $((PASSED + WARNINGS + FAILED))" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"
echo "Report saved to: $REPORT_FILE" | tee -a "$REPORT_FILE"

if [ $FAILED -eq 0 ]; then
    echo "🎉 All critical security tests passed!" | tee -a "$REPORT_FILE"
    exit 0
else
    echo "⚠️  Some security tests failed. Review report." | tee -a "$REPORT_FILE"
    exit 1
fi

