#!/bin/bash
# Quick start script for BOP service with Tailscale

set -e

echo "🚀 Starting BOP Service with Constraint Solver"
echo ""

# Check Tailscale
if command -v tailscale &> /dev/null; then
    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "")
    if [ -n "$TAILSCALE_IP" ]; then
        echo "✅ Tailscale IP: $TAILSCALE_IP"
        echo "   Access at: http://$TAILSCALE_IP:8000"
    else
        echo "⚠️  Tailscale not connected"
    fi
else
    echo "⚠️  Tailscale not installed"
fi

echo ""
echo "📋 Service endpoints:"
echo "   - Health: http://localhost:8000/health"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Metrics: http://localhost:8000/metrics"
echo ""

# Check if constraint solver is available
if uv run python -c "from pran.constraints import PYSAT_AVAILABLE; exit(0 if PYSAT_AVAILABLE else 1)" 2>/dev/null; then
    echo "✅ Constraint solver available"
    USE_CONSTRAINTS="--constraints"
else
    echo "⚠️  Constraint solver not available (install with: uv sync --extra constraints)"
    USE_CONSTRAINTS="--no-constraints"
fi

echo ""
echo "Starting server..."
echo ""

# Start server
uv run pran serve --host 0.0.0.0 --port 8000 $USE_CONSTRAINTS

