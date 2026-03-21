#!/bin/bash
# Mouse Disc - AppImage Installer (Auto-configures by default)
set -e

REPO="OBODA0/mouse-disc"
VERSION="1.0.0"
APPIMAGE_NAME="mouse-disc-${VERSION}-x86_64.AppImage"
INSTALL_DIR="$HOME/Applications"

echo "🖱️  Installing Mouse Disc..."
echo ""

# Create Applications directory
mkdir -p "$INSTALL_DIR"

# Download latest AppImage
echo "Downloading Mouse Disc..."
wget -q --show-progress "https://github.com/${REPO}/releases/download/v${VERSION}/${APPIMAGE_NAME}" -O "${INSTALL_DIR}/${APPIMAGE_NAME}"

# Make executable
chmod +x "${INSTALL_DIR}/${APPIMAGE_NAME}"

echo ""
echo "✅ Mouse Disc installed to ${INSTALL_DIR}/${APPIMAGE_NAME}"
echo ""

# Check desktop environment
DE="${XDG_CURRENT_DESKTOP:-unknown}"
echo "Detected desktop: $DE"
echo ""

# Auto-configure Hyprland
if [ "$DE" = "Hyprland" ]; then
    echo "Auto-configuring Hyprland integration..."
    HYPRLAND_CONF="$HOME/.config/hypr/hyprland.conf"
    BINDING="bind = , mouse:274, exec, ${INSTALL_DIR}/${APPIMAGE_NAME} --show"

    if grep -q "mouse:274.*mouse-disc" "$HYPRLAND_CONF" 2>/dev/null; then
        echo "  ℹ️  Middle-click binding already exists"
    else
        echo "" >> "$HYPRLAND_CONF"
        echo "# Mouse Disc middle-click binding (auto-configured)" >> "$HYPRLAND_CONF"
        echo "$BINDING" >> "$HYPRLAND_CONF"
        echo "  ✅ Middle-click configured"
    fi
    echo ""
fi

# Auto-add to input group (for global capture)
echo "Checking input group membership..."
if id -nG "$USER" | grep -qw "input"; then
    echo "  ✅ Already in 'input' group"
else
    echo "  Adding to 'input' group for global middle-click capture..."
    if sudo usermod -aG input "$USER" 2>/dev/null; then
        echo "  ✅ Added to 'input' group"
        echo ""
        echo "⚠️  IMPORTANT: Log out and back in for changes to take effect!"
    else
        echo "  ❌ Failed to add to group (requires sudo)"
        echo "  You can add yourself manually: sudo usermod -aG input \$USER"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Installation complete!"
echo ""
echo "Run: ${INSTALL_DIR}/${APPIMAGE_NAME}"
echo "Or click the tray icon."
echo ""

if [ "$DE" != "Hyprland" ]; then
    echo "Note: Middle-click requires Hyprland or similar Wayland compositor."
    echo "On other desktops, use the tray icon or configure a hotkey."
    echo ""
fi
