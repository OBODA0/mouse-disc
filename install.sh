#!/bin/bash
# Install Mouse Disc as a system application

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Mouse Disc..."

# Install Python package
cd "$SCRIPT_DIR"
pip3 install --user -e .

# Create desktop entry with correct path
mkdir -p ~/.local/share/applications

# Get the actual install path
PYTHON_USER_BIN="$(python3 -m site --user-base)/bin"

# Update desktop entry
cat > ~/.local/share/applications/mouse-disc.desktop << EOF
[Desktop Entry]
Name=Mouse Disc
Comment=Radial menu for quick shortcuts
Exec=$PYTHON_USER_BIN/mouse-disc
Icon=input-mouse
Type=Application
Categories=System;Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
EOF

# Update desktop database
update-desktop-database ~/.local/share/applications 2>/dev/null || true

echo "Mouse Disc installed!"
echo ""
echo "Run 'mouse-disc' from terminal, or find it in your app menu."
echo "Add to startup:"
echo "  cp ~/.local/share/applications/mouse-disc.desktop ~/.config/autostart/"
