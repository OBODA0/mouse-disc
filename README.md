# Mouse Disc 🖱️

A radial/pie menu that appears on middle mouse click for quick shortcuts on Hyprland/Linux.

> **Note:** This is the development repository. For installation, use the packaged release.

## Installation

### Quick Install (Recommended)

```bash
# Extract to home directory
tar xzf mouse-disc-1.0.0.tar.gz -C ~

# Add to your PATH
mkdir -p ~/.local/bin
ln -sf ~/mouse-disc-1.0.0/mouse-disc ~/.local/bin/

# Add to autostart (optional)
cp ~/mouse-disc-1.0.0/mouse-disc.desktop ~/.config/autostart/
```

Now run `mouse-disc` or find it in your app menu.

### System-wide Install (requires sudo)

```bash
cd ~/Projects/mouse-disc
make package
sudo make install
```

### Build from Source

```bash
cd ~/Projects/mouse-disc
make package
```

Package will be in `build/mouse-disc-1.0.0.tar.gz`

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
