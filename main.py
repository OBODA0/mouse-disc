#!/usr/bin/env python3
"""
Mouse Disc - Universal Radial Menu for Linux
Middle-click is configured via your compositor/DE shortcut (see install.sh).

Usage:
  main.py              # Start tray daemon
  main.py --show       # Show menu at cursor (call this from your shortcut)
  main.py --stop       # Stop daemon
"""
import sys
import os
import subprocess
import socket
import argparse
import threading
from pathlib import Path
from typing import Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import QSocketNotifier, Qt, pyqtSignal, QObject

from config import ConfigManager
from core.single_instance import SingleInstanceLock
from core.window import MouseDiscWindow

SOCKET_PATH = "/tmp/mouse-disc.sock"


def send_signal(cmd: str) -> bool:
    """Send command to running daemon."""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        sock.connect(SOCKET_PATH)
        sock.send(cmd.encode())
        sock.close()
        return True
    except:
        return False


def detect_compositor() -> str:
    """Detect which Wayland compositor is running."""
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return "hyprland"
    if os.environ.get("SWAYSOCK"):
        return "sway"
    if os.environ.get("XDG_CURRENT_DESKTOP", "").lower() in ["kde", "plasma"]:
        return "kde"
    if os.environ.get("XDG_CURRENT_DESKTOP", "").lower() in ["gnome", "ubuntu:gnome"]:
        return "gnome"
    return "unknown"


def get_cursor_pos() -> Tuple[int, int]:
    """Get cursor position."""
    compositor = detect_compositor()

    if compositor == "hyprland":
        try:
            result = subprocess.run(
                ["hyprctl", "cursorpos"],
                capture_output=True, text=True, timeout=0.5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(",")
                if len(parts) == 2:
                    return int(parts[0].strip()), int(parts[1].strip())
        except:
            pass

    # Fallback to center of screen
    app = QApplication.instance()
    if app:
        screen = app.primaryScreen()
        if screen:
            geo = screen.geometry()
            return geo.center().x(), geo.center().y()
    return 0, 0


class MouseDiscDaemon(QObject):
    """System tray daemon with global middle-click support."""

    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("mouse-disc")
        self.app.setQuitOnLastWindowClosed(False)

        self.config_manager = ConfigManager()
        self.window: Optional[MouseDiscWindow] = None
        self.lock: Optional[SingleInstanceLock] = None
        self.socket_server = None
        self.socket_notifier = None
        self.compositor = detect_compositor()

        self._setup_socket()
        self._create_tray()

    def _setup_socket(self):
        """Setup Unix socket for receiving commands."""
        socket_path = Path(SOCKET_PATH)
        if socket_path.exists():
            socket_path.unlink()

        self.socket_server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket_server.bind(str(socket_path))
        self.socket_server.listen(5)
        self.socket_server.setblocking(False)

        self.socket_notifier = QSocketNotifier(
            self.socket_server.fileno(),
            QSocketNotifier.Type.Read
        )
        self.socket_notifier.activated.connect(self._handle_socket)

        # Add Hyprland binding dynamically
        if self.compositor == "hyprland":
            self._add_hyprland_binding()

    def _add_hyprland_binding(self):
        """Add middle-click binding via hyprctl."""
        try:
            # Use wrapper script to avoid argument parsing issues
            subprocess.run(
                ["hyprctl", "keyword", "bind=,mouse:274,exec,/home/oboda/.local/bin/mouse-disc-show"],
                capture_output=True, timeout=1
            )
        except:
            pass

    def _remove_hyprland_binding(self):
        """Remove middle-click binding via hyprctl."""
        try:
            subprocess.run(
                "hyprctl keyword 'unbind=,mouse:274'",
                shell=True, capture_output=True, timeout=1
            )
        except:
            pass

    def _handle_socket(self):
        """Handle incoming socket command."""
        try:
            conn, _ = self.socket_server.accept()
            data = conn.recv(32).decode().strip()
            conn.close()
            if data == "show":
                self.show_menu()
            elif data == "stop":
                self.app.quit()
        except:
            pass

    def _create_tray_icon(self) -> QIcon:
        """Generate tray icon."""
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = size // 2, size // 2
        center_radius = 8
        dot_radius = 5
        spread = 20

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(cx - center_radius, cy - center_radius,
                           center_radius * 2, center_radius * 2)

        colors = ["#ff5050", "#50ff50", "#5050ff", "#ffff50", "#ff50ff", "#50ffff"]
        import math
        for i, color in enumerate(colors):
            angle = i * (360 / len(colors)) - 90
            rad = math.radians(angle)
            dx = cx + spread * math.cos(rad)
            dy = cy + spread * math.sin(rad)
            painter.setBrush(QColor(color))
            painter.drawEllipse(int(dx - dot_radius), int(dy - dot_radius),
                               dot_radius * 2, dot_radius * 2)

        painter.end()
        return QIcon(pixmap)

    def _create_tray(self):
        """Create system tray icon."""
        self.tray = QSystemTrayIcon(self.app)
        self.tray.setIcon(self._create_tray_icon())
        self.tray.setToolTip("Mouse Disc - Middle-click to open")

        tray_menu = QMenu()

        show_action = QAction("Show Menu", self.app)
        show_action.triggered.connect(self.show_menu)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        config_action = QAction("Edit Config", self.app)
        config_action.triggered.connect(self._open_config)
        tray_menu.addAction(config_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self.app)
        quit_action.triggered.connect(self.app.quit)
        tray_menu.addAction(quit_action)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        """Handle tray icon click."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_menu()

    def show_menu(self):
        """Show the radial menu at cursor position."""
        cursor_x, cursor_y = get_cursor_pos()
        self._show_at(cursor_x, cursor_y)

    def _show_at(self, cursor_x: int, cursor_y: int):
        """Show menu at specific position."""
        if self.window is not None:
            self.window.close()
            self.window = None

        self.lock = SingleInstanceLock()
        if not self.lock.acquire():
            self.lock = None
            return

        self.config_manager.config = self.config_manager.load()
        self.window = MouseDiscWindow(
            self.config_manager, self.lock, cursor_x, cursor_y
        )
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _open_config(self):
        """Open config file in default editor."""
        subprocess.Popen(["xdg-open", str(self.config_manager.config_path)])

    def run(self):
        """Run the daemon."""
        print(f"Mouse Disc started (compositor: {self.compositor})")
        print("Middle-click shows the disc. Stop daemon to restore normal middle-click.")
        try:
            result = self.app.exec()
            sys.exit(result)
        finally:
            # Cleanup: remove binding on exit
            if self.compositor == "hyprland":
                self._remove_hyprland_binding()
                print("Removed Hyprland binding, middle-click restored.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Mouse Disc - Radial menu")
    parser.add_argument("--show", action="store_true",
                        help="Show menu (signal to running daemon)")
    parser.add_argument("--stop", action="store_true",
                        help="Stop the daemon")
    args = parser.parse_args()

    if args.show:
        if send_signal("show"):
            sys.exit(0)
        print("Mouse Disc is not running. Start it first: mouse-disc")
        sys.exit(1)

    if args.stop:
        if send_signal("stop"):
            print("Mouse Disc stopped.")
            sys.exit(0)
        print("Mouse Disc is not running.")
        sys.exit(1)

    # Check if daemon already running
    socket_path = Path(SOCKET_PATH)
    if socket_path.exists():
        if send_signal("ping"):
            print("Mouse Disc is already running.")
            sys.exit(0)
        try:
            socket_path.unlink()
        except:
            pass

    # Start daemon
    daemon = MouseDiscDaemon()
    daemon.run()


if __name__ == "__main__":
    main()
