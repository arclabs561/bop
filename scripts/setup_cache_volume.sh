#!/bin/bash
# Setup Fly.io volume for persistent caching

set -e

APP_NAME="${FLY_APP_NAME:-pran-wispy-voice-3017}"
VOLUME_NAME="${VOLUME_NAME:-pran_cache}"
VOLUME_SIZE="${VOLUME_SIZE:-1}"  # GB
REGION="${REGION:-iad}"

echo "💾 Setting up persistent cache volume for BOP"
echo "=============================================="
echo ""
echo "App: $APP_NAME"
echo "Volume: $VOLUME_NAME"
echo "Size: ${VOLUME_SIZE}GB"
echo "Region: $REGION"
echo ""

# Check if volume already exists
echo "📋 Checking for existing volume..."
EXISTING=$(flyctl volumes list -a "$APP_NAME" 2>/dev/null | grep "$VOLUME_NAME" || true)

if [ -n "$EXISTING" ]; then
    echo "✅ Volume $VOLUME_NAME already exists"
    echo ""
    echo "Volume details:"
    flyctl volumes list -a "$APP_NAME" | grep "$VOLUME_NAME"
else
    echo "📦 Creating volume $VOLUME_NAME..."
    flyctl volumes create "$VOLUME_NAME" \
        --size "$VOLUME_SIZE" \
        --region "$REGION" \
        -a "$APP_NAME" \
        --yes
    
    echo ""
    echo "✅ Volume created successfully!"
fi

echo ""
echo "📋 Current volumes:"
flyctl volumes list -a "$APP_NAME"

echo ""
echo "✅ Cache volume setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Deploy app: flyctl deploy -a $APP_NAME"
echo "   2. Verify volume is mounted: flyctl ssh console -a $APP_NAME -C 'ls -la /data'"
echo "   3. Check cache stats: curl -H 'X-API-Key: YOUR_KEY' https://$APP_NAME.fly.dev/cache/stats"
echo ""

