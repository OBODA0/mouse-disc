#!/usr/bin/env python3
"""
Mouse Disc - Radial menu for Hyprland
Middle-click to open, hover to select

Usage:
  main.py             # Tray mode (with signal support for middle-click)
"""
import sys
import subprocess
import socket
from pathlib import Path
from typing import Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction, QCursor, QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import QSocketNotifier, Qt

from config import ConfigManager
from core.single_instance import SingleInstanceLock
from core.window import MouseDiscWindow

SOCKET_PATH = "/tmp/mouse-disc.sock"


def send_show_signal() -> bool:
    """Send show signal to running instance. Returns True if successful."""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        sock.connect(SOCKET_PATH)
        sock.send(b"show")
        sock.close()
        return True
    except (FileNotFoundError, ConnectionRefusedError, socket.timeout):
        return False


def get_cursor_pos_from_hyprland() -> Tuple[int, int]:
    """Get cursor position from hyprland"""
    try:
        result = subprocess.run(
            ["hyprctl", "cursorpos"],
            capture_output=True,
            text=True,
            timeout=0.5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            if len(parts) == 2:
                return int(parts[0].strip()), int(parts[1].strip())
    except Exception:
        pass
    return 0, 0


class MouseDiscApp:
    """Main application class (tray mode with signal support)"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("mouse-disc")
        self.app.setQuitOnLastWindowClosed(False)

        self.config_manager = ConfigManager()
        self.window: Optional[MouseDiscWindow] = None
        self.lock: Optional[SingleInstanceLock] = None
        self.socket_server = None
        self.socket_notifier = None

        self._setup_signal_handler()
        self._create_tray()

    def _setup_signal_handler(self):
        """Setup Unix socket to receive show signals from middle-click"""
        import os
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
        self.socket_notifier.activated.connect(self._handle_signal)

    def _handle_signal(self):
        """Handle incoming show signal"""
        try:
            conn, _ = self.socket_server.accept()
            data = conn.recv(32).decode().strip()
            conn.close()
            if data == "show":
                self.show_menu()
        except Exception:
            pass

    def _show_at(self, cursor_x: int, cursor_y: int):
        """Show menu at specific position"""
        # Close existing window if open
        if self.window is not None:
            self.window.close()
            self.window = None

        # Get lock
        self.lock = SingleInstanceLock()
        if not self.lock.acquire():
            self.lock = None
            return

        # Reload config and show
        self.config_manager.config = self.config_manager.load()
        self.window = MouseDiscWindow(self.config_manager, self.lock, cursor_x, cursor_y)
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _create_tray_icon(self) -> QIcon:
        """Generate a tray icon that looks like a mini mouse disc"""
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = size // 2, size // 2
        center_radius = 8
        dot_radius = 5
        spread = 20

        # Draw center dot (white)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(cx - center_radius, cy - center_radius,
                           center_radius * 2, center_radius * 2)

        # Draw surrounding colored dots like the actual disc
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
        """Create system tray icon"""
        self.tray = QSystemTrayIcon(self.app)
        self.tray.setIcon(self._create_tray_icon())
        self.tray.setToolTip("Mouse Disc - Middle click to open")

        tray_menu = QMenu()
        show_action = QAction("Show", self.app)
        show_action.triggered.connect(self.show_menu)
        tray_menu.addAction(show_action)

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
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_menu()

    def show_menu(self):
        """Show the radial menu at cursor position"""
        cursor_x, cursor_y = get_cursor_pos_from_hyprland()
        self._show_at(cursor_x, cursor_y)

    def _open_config(self):
        """Open config file in editor"""
        subprocess.Popen(["xdg-open", str(self.config_manager.config_path)])

    def run(self):
        """Run the application"""
        print("Mouse Disc started - tray mode")
        sys.exit(self.app.exec())


def main():
    """Entry point - tray mode with signal support"""
    # Check if tray is already running via socket
    socket_path = Path(SOCKET_PATH)
    if socket_path.exists():
        # Try to send signal to existing tray
        if send_show_signal():
            sys.exit(0)
        # Socket exists but no response - stale socket, remove it
        try:
            socket_path.unlink()
        except:
            pass

    # No tray running - start one
    app = MouseDiscApp()
    app.run()


if __name__ == "__main__":
    main()
