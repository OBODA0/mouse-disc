#!/bin/bash
# Mouse Disc - Universal Installer for Linux
# Auto-detects distro and desktop environment to configure
# a native middle-mouse-button shortcut.

set -e

APP_NAME="mouse-disc"
VERSION="1.0.0"
INSTALL_DIR="$HOME/.local/share/mouse-disc"
BIN_DIR="$HOME/.local/bin"
DRY_RUN=0

# Parse args
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
    esac
done

echo "🖱️  Installing Mouse Disc v${VERSION}..."
[ $DRY_RUN -eq 1 ] && echo "   (dry-run: no changes will be written)" || true
echo ""

# ─────────────────────────────────────────────────────────────
#  DETECTION HELPERS
# ─────────────────────────────────────────────────────────────

detect_distro() {
    if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        . /etc/os-release
        echo "${ID:-unknown}"
    else
        echo "unknown"
    fi
}

detect_de() {
    # Wayland compositors (check env vars first)
    if [ -n "$HYPRLAND_INSTANCE_SIGNATURE" ]; then
        echo "hyprland"; return
    fi
    if [ -n "$SWAYSOCK" ]; then
        echo "sway"; return
    fi
    # KDE / Plasma
    if [[ "${XDG_CURRENT_DESKTOP,,}" == *"kde"* ]] || \
       [[ "${XDG_CURRENT_DESKTOP,,}" == *"plasma"* ]]; then
        echo "kde"; return
    fi
    # GNOME variants
    if [[ "${XDG_CURRENT_DESKTOP,,}" == *"gnome"* ]] || \
       [[ "${XDG_CURRENT_DESKTOP,,}" == *"ubuntu"* ]]; then
        echo "gnome"; return
    fi
    # X11 window managers (check binary presence)
    if [ "${XDG_SESSION_TYPE}" = "x11" ]; then
        command -v i3 &>/dev/null && { echo "i3"; return; }
        command -v openbox &>/dev/null && { echo "openbox"; return; }
        command -v bspwm &>/dev/null && { echo "bspwm"; return; }
        command -v xbindkeys &>/dev/null && { echo "xbindkeys"; return; }
    fi
    # Generic Wayland fallback
    [ "${XDG_SESSION_TYPE}" = "wayland" ] && { echo "wayland_generic"; return; }
    echo "unknown"
}

# Backup a config file before modifying it (only once per install)
backup_config() {
    local file="$1"
    local bak="${file}.mouse-disc.bak"
    if [ -f "$file" ] && [ ! -f "$bak" ]; then
        cp "$file" "$bak"
        echo "   📋 Backed up: $bak"
    fi
}

# Check if mouse-disc is already configured in a file
already_configured() {
    local file="$1"
    [ -f "$file" ] && grep -q "mouse-disc" "$file"
}

# Append text to a file (or print in dry-run mode)
safe_append() {
    local file="$1"
    local content="$2"
    if [ $DRY_RUN -eq 1 ]; then
        echo ""
        echo "   [dry-run] Would append to $file:"
        echo "$content" | sed 's/^/     | /'
    else
        backup_config "$file"
        printf "%s\n" "$content" >> "$file"
    fi
}

# ─────────────────────────────────────────────────────────────
#  DEPENDENCIES
# ─────────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CHECKING DEPENDENCIES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

MISSING_DEPS=0

# Check Python3
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 not found"
    MISSING_DEPS=1
else
    echo "✅ Python 3: $(python3 --version)"
fi

# Check pip3
if ! command -v pip3 &>/dev/null && ! python3 -m pip --version &>/dev/null; then
    echo "❌ pip not found"
    MISSING_DEPS=1
else
    echo "✅ pip: available"
fi

# Check PyQt6
if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "❌ PyQt6 not found"
    MISSING_DEPS=1
else
    echo "✅ PyQt6: installed"
fi

echo ""

# Install missing dependencies
if [ $MISSING_DEPS -eq 1 ]; then
    echo "Some dependencies are missing."
    read -rp "Install them now? [Y/n] " response

    if [[ ! "$response" =~ ^[Nn]$ ]]; then
        DISTRO=$(detect_distro)
        echo ""
        echo "Detected distro: $DISTRO"
        echo "Installing dependencies..."
        echo ""

        case "$DISTRO" in
            arch|manjaro|endeavouros|cachyos|garuda)
                sudo pacman -S --noconfirm python python-pip python-pyqt6
                ;;
            debian|ubuntu|linuxmint|pop|elementary)
                sudo apt-get update -q
                sudo apt-get install -y python3 python3-pip python3-pyqt6 || \
                  (sudo apt-get install -y python3 python3-pip && pip3 install --user PyQt6)
                ;;
            fedora)
                sudo dnf install -y python3 python3-pip python3-qt6 || \
                  (sudo dnf install -y python3 python3-pip && pip3 install --user PyQt6)
                ;;
            rhel|centos|rocky|alma)
                sudo dnf install -y python3 python3-pip && pip3 install --user PyQt6
                ;;
            opensuse*|suse*)
                sudo zypper install -y python3 python3-pip python3-qt6 || \
                  (sudo zypper install -y python3 python3-pip && pip3 install --user PyQt6)
                ;;
            *)
                echo "Unknown distro — installing via pip..."
                pip3 install --user PyQt6
                ;;
        esac
    else
        echo ""
        echo "⚠️  Cannot continue without dependencies."
        echo "Install manually: python3, pip3, PyQt6"
        exit 1
    fi
fi

echo ""
echo "✅ All dependencies satisfied!"
echo ""

# ─────────────────────────────────────────────────────────────
#  INSTALL FILES
# ─────────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  INSTALLING MOUSE DISC"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $DRY_RUN -eq 0 ]; then
    mkdir -p "$INSTALL_DIR/core"
    mkdir -p "$INSTALL_DIR/tabs"

    # Local install (run from source dir) or download from GitHub
    if [ -f "mouse-disc-${VERSION}-x86_64.AppImage" ]; then
        echo "Using local AppImage..."
        cp "mouse-disc-${VERSION}-x86_64.AppImage" "$INSTALL_DIR/"
        chmod +x "$INSTALL_DIR/mouse-disc-${VERSION}-x86_64.AppImage"
        echo "Copying source files..."
        cp main.py config.py "$INSTALL_DIR/"
        cp -r core/* "$INSTALL_DIR/core/"
        cp -r tabs/*  "$INSTALL_DIR/tabs/"
    else
        echo "Downloading from GitHub..."
        wget -q --show-progress \
          "https://github.com/OBODA0/mouse-disc/releases/download/v${VERSION}/mouse-disc-${VERSION}-x86_64.AppImage" \
          -O "$INSTALL_DIR/mouse-disc-${VERSION}-x86_64.AppImage"
        chmod +x "$INSTALL_DIR/mouse-disc-${VERSION}-x86_64.AppImage"

        echo "Downloading source files..."
        wget -q "https://github.com/OBODA0/mouse-disc/archive/refs/tags/v${VERSION}.tar.gz" \
          -O "/tmp/mouse-disc-source.tar.gz"
        tar -xzf "/tmp/mouse-disc-source.tar.gz" -C /tmp/
        cp "/tmp/mouse-disc-${VERSION}/main.py" "$INSTALL_DIR/"
        cp "/tmp/mouse-disc-${VERSION}/config.py" "$INSTALL_DIR/"
        cp -r "/tmp/mouse-disc-${VERSION}/core/"* "$INSTALL_DIR/core/"
        cp -r "/tmp/mouse-disc-${VERSION}/tabs/"*  "$INSTALL_DIR/tabs/"
        rm -rf "/tmp/mouse-disc-${VERSION}" "/tmp/mouse-disc-source.tar.gz"
    fi

    # Launcher wrapper
    mkdir -p "$BIN_DIR"
    cat > "$BIN_DIR/mouse-disc" << EOF
#!/bin/bash
exec "$HOME/.local/share/mouse-disc/mouse-disc-${VERSION}-x86_64.AppImage" "\$@"
EOF
    chmod +x "$BIN_DIR/mouse-disc"

    # .desktop file
    mkdir -p "$HOME/.local/share/applications"
    cat > "$HOME/.local/share/applications/mouse-disc.desktop" << EOF
[Desktop Entry]
Name=Mouse Disc
Comment=Radial menu for quick shortcuts
Exec=$BIN_DIR/mouse-disc
Icon=input-mouse
Type=Application
Categories=System;Utility;
X-GNOME-Autostart-enabled=true
EOF
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

    echo "✅ Mouse Disc installed!"
else
    echo "[dry-run] Would install files to $INSTALL_DIR"
    echo "[dry-run] Would create launcher at $BIN_DIR/mouse-disc"
fi

echo ""

# ─────────────────────────────────────────────────────────────
#  AUTOSTART + SHORTCUT SETUP
# ─────────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CONFIGURING SHORTCUT  (auto-detected)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

DE=$(detect_de)
echo "Detected environment: $DE"
echo ""

# ── HYPRLAND ────────────────────────────────────────────────
setup_hyprland() {
    echo "✅ Hyprland detected — configuring native middle-click binding"
    echo ""

    # Find hyprland.conf (check common locations)
    HYPR_CONF=""
    for candidate in \
        "$HOME/.config/hypr/hyprland.conf" \
        "$HOME/.config/hyprland/hyprland.conf" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/hypr/hyprland.conf"
    do
        [ -f "$candidate" ] && { HYPR_CONF="$candidate"; break; }
    done

    if [ -z "$HYPR_CONF" ]; then
        echo "⚠️  Could not find hyprland.conf."
        echo "   Add manually to your hyprland.conf:"
        echo "   exec-once = mouse-disc"
        echo "   bind = , mouse:274, exec, mouse-disc --show"
        return
    fi

    echo "   Config: $HYPR_CONF"

    if already_configured "$HYPR_CONF"; then
        echo "   ⚠️  Already configured — skipping (found 'mouse-disc' in config)"
        return
    fi

    read -rp "   Add middle-click binding to hyprland.conf? [Y/n] " ans
    [[ "$ans" =~ ^[Nn]$ ]] && return

    safe_append "$HYPR_CONF" "
# Mouse Disc — added by installer
# Middle-click binding is added dynamically when daemon starts
exec-once = $BIN_DIR/mouse-disc"

    echo "   ✅ Added! Run 'hyprctl reload' to apply."
}

# ── SWAY ────────────────────────────────────────────────────
setup_sway() {
    echo "✅ Sway detected — configuring native middle-click binding"
    echo ""

    SWAY_CONF=""
    for candidate in \
        "$HOME/.config/sway/config" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/sway/config"
    do
        [ -f "$candidate" ] && { SWAY_CONF="$candidate"; break; }
    done

    if [ -z "$SWAY_CONF" ]; then
        echo "⚠️  Could not find sway config."
        echo "   Add manually to ~/.config/sway/config:"
        echo "   exec $BIN_DIR/mouse-disc"
        echo "   bindsym --whole-window button2 exec $BIN_DIR/mouse-disc --show"
        return
    fi

    echo "   Config: $SWAY_CONF"

    if already_configured "$SWAY_CONF"; then
        echo "   ⚠️  Already configured — skipping"
        return
    fi

    read -rp "   Add middle-click binding to sway config? [Y/n] " ans
    [[ "$ans" =~ ^[Nn]$ ]] && return

    safe_append "$SWAY_CONF" "
# Mouse Disc — added by installer
# Middle-click binding is added dynamically when daemon starts
exec $BIN_DIR/mouse-disc"

    echo "   ✅ Added! Run 'swaymsg reload' to apply."
}

# ── i3 ──────────────────────────────────────────────────────
setup_i3() {
    echo "✅ i3 detected — configuring native middle-click binding"
    echo ""

    I3_CONF=""
    for candidate in \
        "$HOME/.config/i3/config" \
        "$HOME/.i3/config" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/i3/config"
    do
        [ -f "$candidate" ] && { I3_CONF="$candidate"; break; }
    done

    if [ -z "$I3_CONF" ]; then
        echo "⚠️  Could not find i3 config."
        echo "   Add manually to ~/.config/i3/config:"
        echo "   exec --no-startup-id $BIN_DIR/mouse-disc"
        echo "   bindsym button2 exec $BIN_DIR/mouse-disc --show"
        return
    fi

    echo "   Config: $I3_CONF"

    if already_configured "$I3_CONF"; then
        echo "   ⚠️  Already configured — skipping"
        return
    fi

    read -rp "   Add middle-click binding to i3 config? [Y/n] " ans
    [[ "$ans" =~ ^[Nn]$ ]] && return

    safe_append "$I3_CONF" "
# Mouse Disc — added by installer
exec --no-startup-id $BIN_DIR/mouse-disc
bindsym button2 exec $BIN_DIR/mouse-disc --show"

    echo "   ✅ Added! Run 'i3-msg reload' to apply."
}

# ── OPENBOX ─────────────────────────────────────────────────
setup_openbox() {
    echo "✅ Openbox detected — configuring middle-click binding in rc.xml"
    echo ""

    OB_RC=""
    for candidate in \
        "$HOME/.config/openbox/rc.xml" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/openbox/rc.xml"
    do
        [ -f "$candidate" ] && { OB_RC="$candidate"; break; }
    done

    OB_AUTOSTART="${HOME}/.config/openbox/autostart"

    if [ -z "$OB_RC" ]; then
        echo "⚠️  Could not find openbox/rc.xml."
        echo "   Add manually inside <context name=\"Root\"> in your rc.xml:"
        echo '   <mousebind button="Middle" action="Click">'
        echo '     <action name="Execute"><command>mouse-disc --show</command></action>'
        echo '   </mousebind>'
        return
    fi

    echo "   rc.xml: $OB_RC"

    if already_configured "$OB_RC"; then
        echo "   ⚠️  Already configured — skipping"
    else
        read -rp "   Inject middle-click binding into rc.xml? [Y/n] " ans
        if [[ ! "$ans" =~ ^[Nn]$ ]]; then
            if [ $DRY_RUN -eq 1 ]; then
                echo "   [dry-run] Would inject middle-click binding into $OB_RC"
            else
                backup_config "$OB_RC"
                # Insert before the closing </context> of Desktop context
                sed -i 's|</context>|  <mousebind button="Middle" action="Click">\n      <action name="Execute"><command>mouse-disc --show</command></action>\n    </mousebind>\n  </context>|1' "$OB_RC"
                echo "   ✅ Injected! Run 'openbox --reconfigure' to apply."
            fi
        fi
    fi

    # Autostart
    if ! already_configured "$OB_AUTOSTART" 2>/dev/null; then
        read -rp "   Add mouse-disc to Openbox autostart? [Y/n] " ans2
        [[ "$ans2" =~ ^[Nn]$ ]] || safe_append "$OB_AUTOSTART" "mouse-disc &"
    fi
}

# ── BSPWM ───────────────────────────────────────────────────
setup_bspwm() {
    echo "✅ bspwm detected"
    echo ""
    SXHKD_RC="$HOME/.config/sxhkd/sxhkdrc"
    BSPWM_RC="$HOME/.config/bspwm/bspwmrc"

    if [ -f "$SXHKD_RC" ] && ! already_configured "$SXHKD_RC"; then
        read -rp "   Add middle-click binding to sxhkdrc? [Y/n] " ans
        if [[ ! "$ans" =~ ^[Nn]$ ]]; then
            # sxhkd doesn't support mouse buttons directly; use xbindkeys note instead
            echo "   ⚠️  sxhkd does not support mouse button bindings."
            echo "      Use xbindkeys instead (see 'unknown' instructions below)."
        fi
    fi

    # Autostart via bspwmrc
    if [ -f "$BSPWM_RC" ] && ! already_configured "$BSPWM_RC"; then
        read -rp "   Add mouse-disc to bspwmrc autostart? [Y/n] " ans2
        [[ "$ans2" =~ ^[Nn]$ ]] || safe_append "$BSPWM_RC" "mouse-disc &"
    fi

    setup_xbindkeys
}

# ── XBINDKEYS (X11 generic fallback) ────────────────────────
setup_xbindkeys() {
    echo "   Using xbindkeys for global middle-click binding"
    XBINDKEYS_RC="$HOME/.xbindkeysrc"

    if ! command -v xbindkeys &>/dev/null; then
        echo "   ⚠️  xbindkeys not installed. Install it with your package manager."
        echo "      Then add to ~/.xbindkeysrc:"
        echo '      "mouse-disc --show"'
        echo "        b:2"
        return
    fi

    if already_configured "$XBINDKEYS_RC" 2>/dev/null; then
        echo "   ⚠️  Already in ~/.xbindkeysrc — skipping"
        return
    fi

    read -rp "   Add middle-click binding to ~/.xbindkeysrc? [Y/n] " ans
    [[ "$ans" =~ ^[Nn]$ ]] && return

    safe_append "$XBINDKEYS_RC" '
# Mouse Disc — added by installer
"mouse-disc --show"
  b:2'

    echo "   ✅ Added. Restart xbindkeys: killall xbindkeys; xbindkeys"
}

# ── KDE ─────────────────────────────────────────────────────
setup_kde() {
    echo "✅ KDE Plasma detected"
    echo ""
    echo "   ℹ️  KDE does not support binding mouse buttons to global shortcuts"
    echo "   through config files in a reliable cross-distro way."
    echo ""
    echo "   Configuring a keyboard shortcut (Meta+D) instead..."
    echo ""

    KHOTKEYS_DIR="$HOME/.config"

    # Use kwriteconfig5 if available
    if command -v kwriteconfig5 &>/dev/null && [ $DRY_RUN -eq 0 ]; then
        read -rp "   Add Meta+D keyboard shortcut via kwriteconfig5? [Y/n] " ans
        if [[ ! "$ans" =~ ^[Nn]$ ]]; then
            kwriteconfig5 --file kglobalshortcutsrc \
              --group "mouse-disc.desktop" \
              --key "_launch" "Meta+D,none,Mouse Disc"
            echo "   ✅ Keyboard shortcut Meta+D configured."
        fi
    elif [ $DRY_RUN -eq 1 ]; then
        echo "   [dry-run] Would configure Meta+D via kwriteconfig5"
    else
        echo "   kwriteconfig5 not found — configure manually:"
    fi

    echo ""
    echo "   To bind the MIDDLE MOUSE BUTTON in KDE:"
    echo "   System Settings → Input Devices → Mouse → configure button actions"
    echo "   (KDE Wayland: not supported natively for global shortcuts)"
    echo ""

    # Autostart via XDG
    AUTOSTART="$HOME/.config/autostart/mouse-disc.desktop"
    if [ ! -f "$AUTOSTART" ] && [ $DRY_RUN -eq 0 ]; then
        cp "$HOME/.local/share/applications/mouse-disc.desktop" "$AUTOSTART" 2>/dev/null || true
        echo "   ✅ Added to KDE autostart"
    fi
}

# ── GNOME ───────────────────────────────────────────────────
setup_gnome() {
    echo "✅ GNOME detected"
    echo ""
    echo "   ℹ️  GNOME does not support binding mouse buttons to global shortcuts."
    echo "   Configuring a keyboard shortcut (Super+D) instead..."
    echo ""

    if [ $DRY_RUN -eq 1 ]; then
        echo "   [dry-run] Would configure Super+D via gsettings"
    else
        read -rp "   Add Super+D keyboard shortcut via gsettings? [Y/n] " ans
        if [[ ! "$ans" =~ ^[Nn]$ ]]; then
            # Add a custom keybinding using gsettings
            BINDING_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/mouse-disc/"
            gsettings set org.gnome.settings-daemon.plugins.media-keys \
              custom-keybindings \
              "['${BINDING_PATH}']" 2>/dev/null || true
            gsettings set \
              "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${BINDING_PATH}" \
              name "Mouse Disc" 2>/dev/null || true
            gsettings set \
              "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${BINDING_PATH}" \
              command "mouse-disc --show" 2>/dev/null || true
            gsettings set \
              "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${BINDING_PATH}" \
              binding "<Super>d" 2>/dev/null || true
            echo "   ✅ Keyboard shortcut Super+D configured."
        fi
    fi

    echo ""
    echo "   To bind the MIDDLE MOUSE BUTTON in GNOME:"
    echo "   Install 'Input Remapper' (input-remapper) and remap BTN_MIDDLE"
    echo "   to run: mouse-disc --show"
    echo ""

    # Autostart
    AUTOSTART="$HOME/.config/autostart/mouse-disc.desktop"
    if [ $DRY_RUN -eq 0 ] && [ ! -f "$AUTOSTART" ]; then
        cp "$HOME/.local/share/applications/mouse-disc.desktop" "$AUTOSTART" 2>/dev/null || true
        echo "   ✅ Added to GNOME autostart"
    fi
}

# ── UNKNOWN / GENERIC WAYLAND ───────────────────────────────
setup_unknown() {
    echo "⚠️  Could not auto-detect your desktop environment."
    echo ""
    echo "   Add the following to your compositor/WM startup manually:"
    echo ""
    echo "   ┌─ Hyprland ──────────────────────────────────────────────┐"
    echo "   │  exec-once = mouse-disc                                 │"
    echo "   │  bind = , mouse:274, exec, mouse-disc --show            │"
    echo "   └─────────────────────────────────────────────────────────┘"
    echo ""
    echo "   ┌─ Sway ───────────────────────────────────────────────────┐"
    echo "   │  exec mouse-disc                                         │"
    echo "   │  bindsym --whole-window button2 exec mouse-disc --show   │"
    echo "   └──────────────────────────────────────────────────────────┘"
    echo ""
    echo "   ┌─ i3 ─────────────────────────────────────────────────────┐"
    echo "   │  exec --no-startup-id mouse-disc                         │"
    echo "   │  bindsym button2 exec mouse-disc --show                  │"
    echo "   └──────────────────────────────────────────────────────────┘"
    echo ""
    echo "   ┌─ X11 (xbindkeys) ───────────────────────────────────────┐"
    echo '   │  Add to ~/.xbindkeysrc:                                 │'
    echo '   │  "mouse-disc --show"                                    │'
    echo '   │    b:2                                                  │'
    echo "   └─────────────────────────────────────────────────────────┘"
}

# ── AUTOSTART for WMs that don't handle .desktop autostart ──
setup_wm_autostart() {
    local desktop_src="$HOME/.local/share/applications/mouse-disc.desktop"
    local autostart_dir="$HOME/.config/autostart"
    local autostart_dst="$autostart_dir/mouse-disc.desktop"

    if [ $DRY_RUN -eq 0 ] && [ -f "$desktop_src" ]; then
        mkdir -p "$autostart_dir"
        [ ! -f "$autostart_dst" ] && cp "$desktop_src" "$autostart_dst"
    fi
}

# ── Dispatch ────────────────────────────────────────────────
case "$DE" in
    hyprland)
        setup_hyprland
        ;;
    sway)
        setup_sway
        setup_wm_autostart
        ;;
    i3)
        setup_i3
        setup_wm_autostart
        ;;
    openbox)
        setup_openbox
        ;;
    bspwm)
        setup_bspwm
        setup_wm_autostart
        ;;
    xbindkeys)
        setup_xbindkeys
        setup_wm_autostart
        ;;
    kde)
        setup_kde
        ;;
    gnome)
        setup_gnome
        ;;
    wayland_generic)
        echo "⚠️  Generic Wayland compositor detected."
        setup_unknown
        setup_wm_autostart
        ;;
    *)
        setup_unknown
        setup_wm_autostart
        ;;
esac

# ─────────────────────────────────────────────────────────────
#  DONE
# ─────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉  Installation complete!"
echo ""
echo "   Start now:    mouse-disc"
echo "   Show menu:    mouse-disc --show"
echo "   Stop daemon:  mouse-disc --stop"
echo ""
echo "   Middle-click anywhere to open the radial menu."
echo "   (You may need to reload your compositor config first.)"
echo ""
