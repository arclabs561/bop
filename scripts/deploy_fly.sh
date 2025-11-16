#!/bin/bash
# Deploy BOP to Fly.io with web UI
# Includes secret validation and deployment verification

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Deploying BOP to Fly.io..."

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl not found. Install with: curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "🔐 Please login to Fly.io:"
    flyctl auth login
fi

APP_NAME="bop-wispy-voice-3017"
export FLY_APP_NAME="$APP_NAME"

# Validate secrets before deployment
echo ""
echo "🔐 Validating secrets..."
if [ -f "$SCRIPT_DIR/validate_secrets.sh" ]; then
    "$SCRIPT_DIR/validate_secrets.sh" || {
        echo ""
        echo "⚠️  Secret validation failed, but continuing deployment..."
        echo "   You can set secrets after deployment with:"
        echo "   flyctl secrets set KEY=value -a $APP_NAME"
        echo ""
        read -p "Continue with deployment? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Deployment cancelled."
            exit 1
        fi
    }
else
    echo "   ⚠️  validate_secrets.sh not found, skipping validation"
fi

# Deploy
echo ""
echo "📦 Building and deploying..."
flyctl deploy -a "$APP_NAME" --remote-only

# Verify deployment
echo ""
echo "🔍 Verifying deployment..."
if [ -f "$SCRIPT_DIR/verify_deployment.sh" ]; then
    "$SCRIPT_DIR/verify_deployment.sh" || {
        echo ""
        echo "⚠️  Deployment verification had issues"
        echo "   Check logs: flyctl logs -a $APP_NAME --no-tail"
        echo "   Check status: flyctl status -a $APP_NAME"
        exit 1
    }
else
    echo "   ⚠️  verify_deployment.sh not found, skipping verification"
    echo "   Manual verification: curl https://$APP_NAME.fly.dev/health"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Access your app:"
echo "   Public: https://$APP_NAME.fly.dev"
echo ""
echo "📱 For mobile access via Tailscale:"
echo "   1. Set TAILSCALE_AUTHKEY secret: flyctl secrets set TAILSCALE_AUTHKEY=tskey-... -a $APP_NAME"
echo "   2. Get Tailscale IP: flyctl ssh console -a $APP_NAME -C 'tailscale ip -4'"
echo "   3. Access from any Tailscale device: http://<tailscale-ip>:8080"
echo ""
echo "🔍 Quick commands:"
echo "   Status: flyctl status -a $APP_NAME"
echo "   Logs: flyctl logs -a $APP_NAME --no-tail"
echo "   Dashboard: flyctl dashboard -a $APP_NAME"
