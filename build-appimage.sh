#!/bin/bash
# Build Mouse Disc AppImage using appimage-builder
set -e

APP_NAME="mouse-disc"
VERSION="1.0.0"

echo "🖱️  Building Mouse Disc AppImage..."
echo ""
echo "Note: Building AppImage requires appimage-builder to be installed."
echo "Install it with: pip3 install appimage-builder"
echo ""

# Check if appimage-builder is available
if ! command -v appimage-builder &> /dev/null; then
    echo "❌ appimage-builder not found!"
    echo ""
    echo "Install it with:"
    echo "  pip3 install appimage-builder"
    echo ""
    echo "Or download the AppImage:"
    echo "  wget https://github.com/AppImageCrafters/appimage-builder/releases/download/v1.1.0/appimage-builder-1.1.0-x86_64.AppImage"
    echo "  chmod +x appimage-builder-1.1.0-x86_64.AppImage"
    echo "  sudo mv appimage-builder-1.1.0-x86_64.AppImage /usr/local/bin/appimage-builder"
    exit 1
fi

# Build
echo "Building AppImage with appimage-builder..."
appimage-builder --recipe appimage-builder.yml

echo ""
echo "✅ AppImage built successfully!"
echo ""
