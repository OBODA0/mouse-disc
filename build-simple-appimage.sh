#!/bin/bash
# Simple AppImage build for Mouse Disc
# This creates an AppImage that uses system Python but bundles the app

set -e

APP_NAME="mouse-disc"
VERSION="1.0.0"
APPDIR="AppDir"

echo "🖱️  Building simple AppImage..."

# Clean
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy app files
cp main.py config.py "$APPDIR/"
cp -r core tabs "$APPDIR/"

# Create the launcher script that will be the main executable
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
# AppRun for Mouse Disc AppImage
APPDIR="$(dirname "$(readlink -f "$0")")"

# Check for PyQt6
if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "Mouse Disc requires PyQt6"
    echo "Install it with: pip3 install PyQt6"
    exit 1
fi

# Run the app
cd "$APPDIR"
exec python3 "$APPDIR/main.py" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Copy desktop file
cp mouse-disc.desktop "$APPDIR/usr/share/applications/"
cp mouse-disc.desktop "$APPDIR/"
sed -i 's|Exec=.*|Exec=AppRun|' "$APPDIR/mouse-disc.desktop"

# Create a simple icon (placeholder)
# In production, you'd want a real PNG icon
touch "$APPDIR/mouse-disc.png"

# Download AppImage runtime if needed
if [ ! -f "runtime-x86_64" ]; then
    echo "Downloading AppImage runtime..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/runtime-x86_64"
fi

# Build the AppImage manually
echo "Creating AppImage..."

# Calculate size needed
SIZE=$(du -s "$APPDIR" | cut -f1)
SIZE=$((SIZE + 1000))  # Add some padding

# Create squashfs
echo "Creating squashfs..."
mksquashfs "$APPDIR" "${APP_NAME}.squashfs" -root-owned -noappend -comp xz

# Combine runtime + squashfs
echo "Building final AppImage..."
cat runtime-x86_64 "${APP_NAME}.squashfs" > "${APP_NAME}-${VERSION}-x86_64.AppImage"
chmod +x "${APP_NAME}-${VERSION}-x86_64.AppImage"

# Cleanup
rm -f "${APP_NAME}.squashfs"

echo ""
echo "✅ Built: ${APP_NAME}-${VERSION}-x86_64.AppImage"
echo ""
echo "Note: This AppImage requires system Python3 and PyQt6."
echo "For a fully standalone version, more bundling is needed."
