#!/bin/bash
# Validate required secrets before deployment
# Checks that all necessary API keys and configuration are set

set -e

APP_NAME="${FLY_APP_NAME:-pran-wispy-voice-3017}"

echo "🔐 Validating secrets for $APP_NAME..."

# Check if flyctl is available
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl not found. Install with: curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io"
    echo "   Run: flyctl auth login"
    exit 1
fi

# Get current secrets
echo "📋 Fetching current secrets..."
SECRETS=$(flyctl secrets list -a "$APP_NAME" 2>/dev/null || echo "")

if [ -z "$SECRETS" ]; then
    echo "⚠️  No secrets found. App may not exist yet."
    echo "   This is OK for first deployment."
    echo ""
    echo "📝 Required secrets (set after first deploy):"
    echo "   - At least one LLM backend: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY"
    echo "   - Optional: MCP tool keys (PERPLEXITY_API_KEY, FIRECRAWL_API_KEY, TAVILY_API_KEY)"
    echo "   - Optional: BOP_API_KEY (for API authentication)"
    echo "   - Optional: TAILSCALE_AUTHKEY (for Tailscale private network)"
    exit 0
fi

# Check for LLM backends (at least one required)
echo ""
echo "🤖 Checking LLM backends..."
HAS_LLM=false

if echo "$SECRETS" | grep -q "OPENAI_API_KEY"; then
    echo "   ✅ OPENAI_API_KEY is set"
    HAS_LLM=true
fi

if echo "$SECRETS" | grep -q "ANTHROPIC_API_KEY"; then
    echo "   ✅ ANTHROPIC_API_KEY is set"
    HAS_LLM=true
fi

if echo "$SECRETS" | grep -q "GEMINI_API_KEY"; then
    echo "   ✅ GEMINI_API_KEY is set"
    HAS_LLM=true
fi

if [ "$HAS_LLM" = false ]; then
    echo "   ❌ No LLM backend API keys found"
    echo "   Set at least one:"
    echo "      flyctl secrets set OPENAI_API_KEY=sk-... -a $APP_NAME"
    echo "      flyctl secrets set ANTHROPIC_API_KEY=sk-ant-... -a $APP_NAME"
    echo "      flyctl secrets set GEMINI_API_KEY=... -a $APP_NAME"
    exit 1
fi

# Check MCP tools (optional but recommended)
echo ""
echo "🔧 Checking MCP tools (optional)..."
MCP_COUNT=0

if echo "$SECRETS" | grep -q "PERPLEXITY_API_KEY"; then
    echo "   ✅ PERPLEXITY_API_KEY is set"
    MCP_COUNT=$((MCP_COUNT + 1))
fi

if echo "$SECRETS" | grep -q "FIRECRAWL_API_KEY"; then
    echo "   ✅ FIRECRAWL_API_KEY is set"
    MCP_COUNT=$((MCP_COUNT + 1))
fi

if echo "$SECRETS" | grep -q "TAVILY_API_KEY"; then
    echo "   ✅ TAVILY_API_KEY is set"
    MCP_COUNT=$((MCP_COUNT + 1))
fi

if [ $MCP_COUNT -eq 0 ]; then
    echo "   ⚠️  No MCP tool keys found (research features will be limited)"
    echo "   Recommended: Set at least PERPLEXITY_API_KEY for research"
else
    echo "   ✅ $MCP_COUNT MCP tool(s) configured"
fi

# Check API key (optional but recommended for production)
echo ""
echo "🔒 Checking API authentication..."
if echo "$SECRETS" | grep -q "BOP_API_KEY"; then
    echo "   ✅ BOP_API_KEY is set (API authentication enabled)"
else
    echo "   ⚠️  BOP_API_KEY not set (endpoints will be publicly accessible)"
    echo "   Recommended for production:"
    echo "      flyctl secrets set BOP_API_KEY=\$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))') -a $APP_NAME"
fi

# Check Tailscale (optional)
echo ""
echo "🌐 Checking Tailscale..."
if echo "$SECRETS" | grep -q "TAILSCALE_AUTHKEY"; then
    echo "   ✅ TAILSCALE_AUTHKEY is set (private network access enabled)"
else
    echo "   ℹ️  TAILSCALE_AUTHKEY not set (optional, for private network access)"
fi

# Check constraint solver config
echo ""
echo "🧮 Checking constraint solver..."
if echo "$SECRETS" | grep -q "BOP_USE_CONSTRAINTS"; then
    CONSTRAINT_VALUE=$(echo "$SECRETS" | grep "BOP_USE_CONSTRAINTS" | awk '{print $2}')
    echo "   ✅ BOP_USE_CONSTRAINTS=$CONSTRAINT_VALUE"
else
    echo "   ℹ️  BOP_USE_CONSTRAINTS not set (defaults to true in fly.toml)"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Secret validation complete!"
echo ""
echo "📊 Summary:"
echo "   LLM Backend: ✅"
if [ $MCP_COUNT -gt 0 ]; then
    echo "   MCP Tools: ✅ ($MCP_COUNT configured)"
else
    echo "   MCP Tools: ⚠️  (none configured)"
fi
if echo "$SECRETS" | grep -q "BOP_API_KEY"; then
    echo "   API Auth: ✅"
else
    echo "   API Auth: ⚠️  (not configured)"
fi
echo ""
echo "🚀 Ready to deploy!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

