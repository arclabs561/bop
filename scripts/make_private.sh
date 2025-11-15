#!/bin/bash
# Make Fly.io app private (remove public IPs, Tailscale-only access)

set -e

APP_NAME="bop-wispy-voice-3017"

echo "🔒 Making $APP_NAME private (Tailscale-only access)..."

# List current IPs
echo "📋 Current IP addresses:"
flyctl ips list -a "$APP_NAME"

# Release public IPv4
echo ""
echo "🗑️  Releasing public IPv4 addresses..."
PUBLIC_IPV4=$(flyctl ips list -a "$APP_NAME" | grep "v4" | grep -v "private" | awk '{print $2}' | head -1)
if [ -n "$PUBLIC_IPV4" ] && [ "$PUBLIC_IPV4" != "IP" ]; then
    echo "   Releasing: $PUBLIC_IPV4"
    flyctl ips release "$PUBLIC_IPV4" -a "$APP_NAME" || echo "   (Already released or not found)"
else
    echo "   No public IPv4 found"
fi

# Release public IPv6
echo ""
echo "🗑️  Releasing public IPv6 addresses..."
PUBLIC_IPV6=$(flyctl ips list -a "$APP_NAME" | grep "v6" | grep -v "private" | awk '{print $2}' | head -1)
if [ -n "$PUBLIC_IPV6" ] && [ "$PUBLIC_IPV6" != "IP" ]; then
    echo "   Releasing: $PUBLIC_IPV6"
    flyctl ips release "$PUBLIC_IPV6" -a "$APP_NAME" || echo "   (Already released or not found)"
else
    echo "   No public IPv6 found"
fi

echo ""
echo "✅ App is now private!"
echo ""
echo "📱 Access methods:"
echo "   1. Tailscale: http://<tailscale-ip>:8080"
echo "   2. Fly proxy: flyctl proxy 8080:8080 -a $APP_NAME"
echo ""
echo "🔍 Verify:"
echo "   flyctl ips list -a $APP_NAME"

