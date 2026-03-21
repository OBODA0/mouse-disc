# Mouse Disc 🖱️

A radial/pie menu that appears on middle mouse click for quick shortcuts on Hyprland/Linux.

![Demo](demo.png)

## Installation

### For Users (Non-coders)

#### Option 1: System Install (Recommended)

```bash
# Clone or download the project
cd ~/Projects/mouse-disc

# Build the package
make package

# Install system-wide (requires sudo)
make install
```

This installs to `/opt/mouse-disc` and creates a `mouse-disc` command.

#### Option 2: User Install (No sudo needed)

```bash
# Build and extract to your home directory
cd ~/Projects/mouse-disc
make package
tar xzf build/mouse-disc-1.0.0.tar.gz -C ~

# Create symlink
mkdir -p ~/.local/bin
ln -sf ~/mouse-disc-1.0.0/mouse-disc ~/.local/bin/

# Add to autostart
cp ~/mouse-disc-1.0.0/mouse-disc.desktop ~/.config/autostart/
```

### For Developers

```bash
# Install dependencies
pip install -r requirements.txt

# Run from source
python3 main.py
```

## Auto-start on Login

Add to your Hyprland config:

```conf
exec-once = mouse-disc
```

Or copy the desktop file:
```bash
cp /usr/share/applications/mouse-disc.desktop ~/.config/autostart/
```

## Usage

- **Middle-click** anywhere to open the menu
- **Hover** over items to select
- **Click** to activate
- **ESC** or **Right-click** to close
- Use mouse **back/forward** buttons to switch workspaces

## Hyprland Integration

Add to your `~/.config/hypr/hyprland.conf`:

```conf
source = /usr/share/applications/mouse-disc.desktop

# Or manually:
exec-once = mouse-disc
bind = , mouse:274, exec, mouse-disc --show
```

## Configuration

Edit `~/.config/mouse-disc/config.json` to customize:
- Menu items and apps
- Colors
- Keyboard shortcuts

## Features

- 🎯 Radial menu with smooth animations
- 🎨 Customizable colors and actions
- ⌨️ Keyboard navigation (ESC to close)
- 🔧 Hyprland native integration
- 📦 System tray support
- ⚡ Instant show with daemon mode

## Uninstall

```bash
make uninstall
```

## License

MIT
