# Mouse Disc 🖱️

A radial/pie menu for Linux that appears on middle mouse click. Built for Hyprland with support for other Wayland compositors and X11 window managers.

![Mouse Disc Demo](https://github.com/OBODA0/mouse-disc/raw/main/demo.png)

## Features

- 🎯 **Radial Menu** - 8-position pie menu with smooth animations
- 📂 **Submenus** - Expandable menus for Apps, Controls, Music, AI, and Power
- 🎚️ **Brightness Bar** - Curved brightness slider in Controls submenu
- 🔘 **Toggle Items** - WiFi, Bluetooth, Mute speakers, Mute mic with state sync
- 🎨 **Customizable** - JSON configuration for items, colors, and styling
- 🔧 **Multi-DE Support** - Hyprland, Sway, i3, Openbox, KDE, GNOME
- 📦 **System Tray** - Runs as daemon with tray icon
- ⚡ **Fast** - Native Python + PyQt6, socket-based IPC

## Roadmap / Coming Soon

- 🖥️ **Electron Configuration App** - Visual editor for customizing menu items, colors, and keybindings without editing JSON
- 🎯 **App-Specific Context Menus** - Different radial menus that appear based on the active application (e.g., media controls when focused on video player, Git commands in terminal, etc.)
- 🪟 **Windows Support** - Port to Windows with global hotkey registration and native system integration
- 🔗 **Plugin System** - Load custom Python plugins for advanced actions
- 📝 **More Presets** - Built-in configurations for popular workflows

## Menu Structure

```
                    Music (▶)
                      │
        AI (◈) ───┬───┴───┬─── Editor (</>)
                  │       │
    Controls (⫚)─┤   ●   ├─ Screenshot (◻)
                  │       │
        Apps (▦)──┴───┬───┴─── Terminal (>_)
                      │
                   Power (⏻)
```

### Submenus

- **Music**: Previous, Backward 10s, Play/Pause, Forward 10s, Next
- **Apps**: Obsidian, Antigravity, Zen Browser, ZapZap
- **Controls**: WiFi toggle, Bluetooth toggle, Mute speakers, Mute mic + Brightness bar
- **AI**: Perplexity, Gemini, Claude, ChatGPT
- **Power**: Shutdown, Reboot, Suspend, Lock

## Installation

### Prerequisites

- Python 3.8+
- PyQt6 (`pip install PyQt6` or system package)

### Option 1: Universal Installer (Recommended)

```bash
git clone https://github.com/OBODA0/mouse-disc.git
cd mouse-disc
./install.sh
```

The installer auto-detects your desktop environment and configures the middle-click binding.

### Option 2: AppImage

```bash
# Build the AppImage
./build-simple-appimage.sh

# Install
./install.sh
```

### Option 3: Manual Install

```bash
# Copy files
mkdir -p ~/.local/share/mouse-disc
cp -r main.py config.py core tabs ~/.local/share/mouse-disc/

# Create launcher
mkdir -p ~/.local/bin
cat > ~/.local/bin/mouse-disc << 'EOF'
#!/bin/bash
exec python3 ~/.local/share/mouse-disc/main.py "$@"
EOF
chmod +x ~/.local/bin/mouse-disc

# Add to your Hyprland config:
# exec-once = mouse-disc
# bind = , mouse:274, exec, mouse-disc --show
```

## Usage

- **Middle-click** anywhere to open the menu
- **Hover** over items to select
- **Click** to activate
- **ESC** or **Right-click** to close without selecting
- **Click center** to go back (in submenus) or close (main menu)
- **Scroll** on brightness bar to adjust brightness (Controls submenu)

### Commands

```bash
mouse-disc           # Start daemon (with system tray)
mouse-disc --show    # Show menu (for keybinding)
mouse-disc --stop    # Stop daemon
```

## Configuration

Edit `~/.config/mouse-disc/config.json`:

```json
{
  "items": [
    {"id": "music", "action_type": "menu", "children": [...]},
    {"id": "editor", "action": "code", "action_type": "app"},
    {"id": "terminal", "action": "kitty", "action_type": "app"}
  ],
  "main_style": {
    "spread_radius": 122,
    "dot_radius": 35,
    "hover_growth": 5,
    "hit_radius": 50
  },
  "sub_style": {
    "spread_radius": 234,
    "dot_radius": 35
  },
  "colors": {
    "normal": "#e8e8e8",
    "hover": "#ffffff",
    "toggle_on": "#ff5050",
    "icon": "#282828"
  }
}
```

## Desktop Environment Setup

### Hyprland

Already configured by installer. Manual setup:

```conf
exec-once = mouse-disc
bind = , mouse:274, exec, mouse-disc --show
```

### Sway

```conf
exec mouse-disc
bindsym --whole-window button2 exec mouse-disc --show
```

### i3

```conf
exec --no-startup-id mouse-disc
bindsym button2 exec mouse-disc --show
```

### KDE Plasma

Uses keyboard shortcut (Meta+D) - mouse button binding requires Input Remapper.

### GNOME

Uses keyboard shortcut (Super+D) - mouse button binding requires Input Remapper.

## Architecture

```
main.py              # Daemon with tray icon and socket server
├── config.py        # Configuration management
├── core/
│   ├── window.py    # Main radial menu window (PyQt6)
│   ├── actions.py   # Action execution handlers
│   ├── icons.py     # Icon drawing functions
│   ├── menu_level.py # Menu stack management
│   └── base_tab.py  # Tab base classes
└── tabs/
    ├── __init__.py  # Auto-discovery registry
    ├── music.py     # Menu with children
    ├── controls/__init__.py  # Controls menu + brightness bar
    ├── apps/        # App launcher children
    ├── ai/          # AI service children
    ├── power/       # Power option children
    └── music/       # Music control children
```

### Adding Custom Tabs

Create a new file in `tabs/`:

```python
from core.base_tab import Tab
from PyQt6.QtGui import QPainter, QColor

def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    painter.drawEllipse(int(cx - size/2), int(cy - size/2), int(size), int(size))

def _action():
    print("Custom action!")
    return True  # Close menu

tab = Tab(
    id="myapp",
    label="My App",
    action="myapp",
    action_type="app",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
```

## Uninstall

```bash
# Stop daemon
mouse-disc --stop

# Remove files
rm -rf ~/.local/share/mouse-disc
rm -f ~/.local/bin/mouse-disc
rm -f ~/.local/share/applications/mouse-disc.desktop
rm -f ~/.config/autostart/mouse-disc.desktop

# Remove Hyprland config lines (manual)
```

## Troubleshooting

### Middle-click doesn't work

1. Check daemon is running: `ps aux | grep mouse-disc`
2. Try manual show: `mouse-disc --show`
3. Check Hyprland config has the bind: `grep mouse:274 ~/.config/hypr/hyprland.conf`

### Only one tab shows

The registry auto-discovers tabs. Check for import errors:

```bash
cd ~/.local/share/mouse-disc
python3 -c "from tabs import get_registry; r = get_registry(); print(r._tabs.keys())"
```

### AppImage won't run

The AppImage requires system Python3 and PyQt6:

```bash
# Arch
sudo pacman -S python python-pyqt6

# Ubuntu/Debian
sudo apt install python3 python3-pyqt6
```

## License

MIT

## Contributing

Pull requests welcome! The modular tab system makes it easy to add new menu items.
