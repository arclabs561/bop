#!/bin/bash
# Continuous Improvement Cycle Runner

set -e

echo "🔄 Starting Continuous Improvement Cycle"
echo "=========================================="

# Step 1: Start server
echo ""
echo "1️⃣  Starting server..."
uv run python -m pran.server > /tmp/pran-server-cycle.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > /tmp/pran-server-cycle.pid

# Wait for server
echo "   Waiting for server..."
for i in {1..15}; do
  if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "   ✅ Server ready"
    break
  fi
  sleep 1
done

# Step 2: Run accessibility audit
echo ""
echo "2️⃣  Running accessibility audit..."
npx playwright test tests/accessibility_audit.mjs --project=chromium --reporter=list 2>&1 | tail -30 || echo "   ⚠️  Some tests failed (check output above)"

# Step 3: Run quick validation
echo ""
echo "3️⃣  Running quick validation..."
npx playwright test tests/validate_improvements.mjs --project=chromium --reporter=list 2>&1 | tail -20 || echo "   ⚠️  Some tests failed"

# Step 4: Generate improvement report
echo ""
echo "4️⃣  Generating improvement report..."
node tests/visual_improvement_tracker.mjs 2>&1 || echo "   ⚠️  Tracker failed"

# Step 5: Check contrast
echo ""
echo "5️⃣  Checking color contrast..."
uv run python scripts/check_contrast.py 2>&1 || echo "   ⚠️  Contrast check failed"

# Cleanup
echo ""
echo "6️⃣  Cleaning up..."
kill $SERVER_PID 2>/dev/null || true
rm /tmp/pran-server-cycle.pid 2>/dev/null || true

echo ""
echo "✅ Improvement cycle complete!"
echo ""
echo "Next steps:"
echo "  • Review test results above"
echo "  • Implement any identified fixes"
echo "  • Run again to validate"
echo "  • Continue iterating"
