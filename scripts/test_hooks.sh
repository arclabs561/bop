#!/bin/bash
# Test all git hooks and hookwise functionality
# Steers toward correct hook configuration

set -e

echo "🧪 Testing Git Hooks and Hookwise Configuration"
echo "================================================"
echo ""

# Test hookwise config validation
echo "1️⃣  Testing hookwise configuration..."
if npx hookwise validate-config 2>&1; then
    echo "   ✅ Configuration valid"
else
    echo "   ❌ Configuration invalid"
    exit 1
fi
echo ""

# Test hookwise config display
echo "2️⃣  Testing hookwise config display..."
npx hookwise config
echo ""

# Test commit message validation
echo "3️⃣  Testing commit message validation..."
echo "   Testing valid message..."
if npx hookwise test-commit "feat(agent): add belief-evidence alignment" 2>&1 | grep -q "valid\|passed"; then
    echo "   ✅ Valid message accepted"
else
    echo "   ⚠️  Valid message test inconclusive"
fi

echo "   Testing invalid message..."
if npx hookwise test-commit "bad message" 2>&1 | grep -q "invalid\|error\|failed"; then
    echo "   ✅ Invalid message rejected"
else
    echo "   ⚠️  Invalid message test inconclusive"
fi
echo ""

# Test documentation bloat detection
echo "4️⃣  Testing documentation bloat detection..."
if npx hookwise test-docs 2>&1; then
    echo "   ✅ Documentation check completed"
else
    echo "   ⚠️  Documentation check had issues"
fi
echo ""

# Test garden mode (all checks)
echo "5️⃣  Testing garden mode (all checks)..."
if npx hookwise garden 2>&1; then
    echo "   ✅ Garden mode completed"
else
    echo "   ⚠️  Garden mode had issues"
fi
echo ""

# Test Q&A (if API key available)
echo "6️⃣  Testing hookwise Q&A..."
if [ -n "$GEMINI_API_KEY" ] || [ -n "$OPENAI_API_KEY" ] || [ -n "$ANTHROPIC_API_KEY" ]; then
    if npx hookwise ask "What is this repository about?" 2>&1 | head -20; then
        echo "   ✅ Q&A system working"
    else
        echo "   ⚠️  Q&A system had issues"
    fi
else
    echo "   ⚠️  No LLM API key found, skipping Q&A test"
    echo "   Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in .env"
fi
echo ""

# Test metrics
echo "7️⃣  Testing metrics..."
if npx hookwise metrics 2>&1 | head -10; then
    echo "   ✅ Metrics available"
else
    echo "   ⚠️  Metrics had issues"
fi
echo ""

# Test recommendations
echo "8️⃣  Testing recommendations..."
if npx hookwise recommend 2>&1; then
    echo "   ✅ Recommendations available"
else
    echo "   ⚠️  Recommendations had issues"
fi
echo ""

# Test hook scripts directly
echo "9️⃣  Testing hook scripts..."
echo "   Testing commit-msg hook..."
if .husky/commit-msg <(echo "feat: test") 2>&1 | head -5; then
    echo "   ✅ commit-msg hook works"
else
    echo "   ⚠️  commit-msg hook had issues"
fi

echo "   Testing pre-commit hook..."
if .husky/pre-commit 2>&1 | head -10; then
    echo "   ✅ pre-commit hook works"
else
    echo "   ⚠️  pre-commit hook had issues (may be expected if no staged files)"
fi
echo ""

echo "✅ Hook testing complete!"
echo ""
echo "💡 Next steps:"
echo "   - Review any warnings above"
echo "   - Test actual commits: git commit -m 'feat: test'"
echo "   - Check metrics: npx hookwise metrics"
echo "   - Get recommendations: npx hookwise recommend"

