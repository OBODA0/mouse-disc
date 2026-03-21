#!/usr/bin/env python3
"""
Mouse Disc - Radial menu for Hyprland
Middle-click to open, hover to select

Usage:
  main.py --daemon    # Start background daemon (run at startup)
  main.py --show      # Show menu instantly (called from hyprland)
  main.py             # Tray mode
"""
import sys
import subprocess
from pathlib import Path
from typing import Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction, QCursor

from config import ConfigManager
from core.single_instance import SingleInstanceLock
from core.window import MouseDiscWindow
from core.daemon import SignalHandler, send_show_signal


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


class MouseDiscDaemon:
    """Daemon that keeps QApplication warm for instant show"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("mouse-disc-daemon")
        self.app.setQuitOnLastWindowClosed(False)

        self.config_manager = ConfigManager()
        self.window: Optional[MouseDiscWindow] = None
        self.lock: Optional[SingleInstanceLock] = None

        # Setup signal handler for instant show
        self.signal_handler = SignalHandler()
        self.signal_handler.show_requested.connect(self._on_show_requested)

    def _on_show_requested(self, cursor_x: int, cursor_y: int):
        """Handle show request from client"""
        # Close existing window if open
        if self.window is not None:
            self.window.close()
            self.window = None

        # Get fresh lock
        self.lock = SingleInstanceLock()
        if not self.lock.acquire():
            self.lock = None
            return

        # Reload config
        self.config_manager.config = self.config_manager.load()

        # Create and show window
        self.window = MouseDiscWindow(self.config_manager, self.lock, cursor_x, cursor_y)
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def run(self):
        """Run the daemon"""
        print("Mouse Disc daemon started")
        print("Use 'main.py --show' to display menu instantly")
        try:
            sys.exit(self.app.exec())
        finally:
            self.signal_handler.cleanup()


class MouseDiscApp:
    """Main application class (tray mode + daemon)"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("mouse-disc")
        self.app.setQuitOnLastWindowClosed(False)

        self.config_manager = ConfigManager()
        self.window: Optional[MouseDiscWindow] = None
        self.lock: Optional[SingleInstanceLock] = None

        # Setup signal handler for instant show from middle-click
        self.signal_handler = SignalHandler()
        self.signal_handler.show_requested.connect(self._on_show_requested)

        self._create_tray()

    def _on_show_requested(self, cursor_x: int, cursor_y: int):
        """Handle show request from middle-click"""
        self._show_at(cursor_x, cursor_y)

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

    def _create_tray(self):
        """Create system tray icon"""
        self.tray = QSystemTrayIcon(self.app)
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
        print("Mouse Disc started - tray mode with daemon")
        try:
            sys.exit(self.app.exec())
        finally:
            self.signal_handler.cleanup()


def main():
    """Entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        # Daemon mode - keep warm for instant show
        lock = SingleInstanceLock()
        if not lock.acquire():
            print("Daemon already running")
            sys.exit(0)

        daemon = MouseDiscDaemon()
        # Keep lock by storing it
        daemon._daemon_lock = lock
        daemon.run()

    elif len(sys.argv) > 1 and sys.argv[1] == "--show":
        # Show mode - try daemon first, fall back to direct
        cursor_x, cursor_y = get_cursor_pos_from_hyprland()

        # Try to signal daemon (instant)
        if send_show_signal(cursor_x, cursor_y):
            sys.exit(0)

        # Daemon not running - start it in background and show
        print("Starting daemon...")
        subprocess.Popen([sys.executable, __file__, "--daemon"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)

        # Wait a bit for daemon to start, then signal
        import time
        time.sleep(0.15)

        # Retry signal
        if send_show_signal(cursor_x, cursor_y):
            sys.exit(0)

        # Fallback: direct mode (slow but works)
        print("Fallback to direct mode")
        app = QApplication(sys.argv)
        config_manager = ConfigManager()
        lock = SingleInstanceLock()
        if lock.acquire():
            window = MouseDiscWindow(config_manager, lock, cursor_x, cursor_y)
            window.show()
            sys.exit(app.exec())

    else:
        # Tray mode
        app = MouseDiscApp()
        app.run()


if __name__ == "__main__":
    main()
