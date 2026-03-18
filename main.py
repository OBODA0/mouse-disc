#!/usr/bin/env python3
"""
Mouse Disc - Radial menu for Hyprland
Middle-click to open, hover to select

Refactored modular version - entry point
"""
import sys
import subprocess
from pathlib import Path
from typing import Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction, QCursor

from config import ConfigManager
from core.single_instance import SingleInstanceLock
from core.window import MouseDiscWindow


class MouseDiscApp:
    """Main application class"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("mouse-disc")
        self.app.setQuitOnLastWindowClosed(False)

        self.config_manager = ConfigManager()
        self.window: Optional[MouseDiscWindow] = None

        self._create_tray()

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
        """Show the radial menu"""
        # Check lock first
        lock = SingleInstanceLock()
        if not lock.acquire():
            # Another instance is running, close it first
            return

        if self.window is not None:
            self.window.close()
            self.window = None

        # Get cursor position from hyprland
        cursor_x, cursor_y = get_cursor_pos_from_hyprland()

        # Reload config
        self.config_manager.config = self.config_manager.load()

        self.window = MouseDiscWindow(self.config_manager, lock, cursor_x, cursor_y)
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _open_config(self):
        """Open config file in editor"""
        subprocess.Popen(["xdg-open", str(self.config_manager.config_path)])

    def run(self):
        """Run the application"""
        sys.exit(self.app.exec())


def get_cursor_pos_from_hyprland() -> Tuple[int, int]:
    """Get cursor position from hyprland before QApplication starts"""
    try:
        result = subprocess.run(
            ["hyprctl", "cursorpos"],
            capture_output=True,
            text=True,
            timeout=0.5
        )
        if result.returncode == 0:
            # Parse output like "1234, 567"
            parts = result.stdout.strip().split(",")
            if len(parts) == 2:
                return int(parts[0].strip()), int(parts[1].strip())
    except Exception:
        pass
    return 0, 0


def main():
    """Entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        # Direct show mode (called from hyprland binding)
        # Get cursor position BEFORE creating QApplication (which resets it to 0,0)
        cursor_x, cursor_y = get_cursor_pos_from_hyprland()

        # Check single instance lock
        lock = SingleInstanceLock()
        if not lock.acquire():
            # Another instance is running - kill it and open new one
            subprocess.run(["pkill", "-f", "main.py --show"])
            import time
            time.sleep(0.1)
            if not lock.acquire():
                print("Could not acquire lock")
                sys.exit(1)

        app = QApplication(sys.argv)
        config_manager = ConfigManager()
        window = MouseDiscWindow(config_manager, lock, cursor_x, cursor_y)
        window.show()
        sys.exit(app.exec())
    else:
        # Tray mode
        app = MouseDiscApp()
        app.run()


if __name__ == "__main__":
    from typing import Optional  # Import for type hints
    main()
