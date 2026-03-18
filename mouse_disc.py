"""
Mouse Disc - Radial menu for Hyprland
Middle-click to open, hover to select
"""
import sys
import math
import subprocess
import fcntl
from pathlib import Path
from typing import List, Tuple, Optional

from PyQt6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QPainter, QColor, QPen, QAction, QCursor, QIcon, QFont
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QTimer

from config import ConfigManager, DiscItem, MenuStyle
from icons import draw_icon
from actions import ActionExecutor


class SingleInstanceLock:
    """Ensure only one instance of the menu is running"""
    def __init__(self, lock_path: str = "/tmp/mouse-disc.lock"):
        self.lock_path = Path(lock_path)
        self.lock_file = None

    def acquire(self) -> bool:
        """Try to acquire lock. Returns True if successful, False if already locked."""
        self.lock_file = open(self.lock_path, 'w')
        try:
            fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except IOError:
            self.lock_file.close()
            self.lock_file = None
            return False

    def release(self):
        """Release the lock"""
        if self.lock_file:
            fcntl.flock(self.lock_file, fcntl.LOCK_UN)
            self.lock_file.close()
            self.lock_file = None
        if self.lock_path.exists():
            try:
                self.lock_path.unlink()
            except:
                pass


class MenuLevel:
    """Represents one level of menu (main or submenu)"""
    def __init__(self, items: List[DiscItem], parent_angle: float = 0,
                 level: int = 0, parent_item: Optional[DiscItem] = None):
        self.items = items
        self.parent_angle = parent_angle  # Angle of parent (for submenus)
        self.level = level  # 0 = main, 1 = first submenu, etc.
        self.parent_item = parent_item
        self.hovered_index = -1
        self.expanded_child = None  # Which child submenu is expanded

    def get_style(self, config) -> MenuStyle:
        """Get the style for this menu level"""
        if self.level == 0:
            return config.main_style
        else:
            return config.sub_style


class MouseDiscWindow(QWidget):
    """Main radial menu window"""

    def __init__(self, config_manager: ConfigManager, lock: SingleInstanceLock,
                 cursor_x: int = 0, cursor_y: int = 0):
        super().__init__()
        self.config_manager = config_manager
        self.config = config_manager.config
        self.executor = ActionExecutor(self._on_toggle_changed)
        self.lock = lock

        # Menu stack: [main, submenu1, submenu2, ...]
        self.menu_stack: List[MenuLevel] = []

        # Use provided cursor position (from hyprland) or try to get from Qt
        if cursor_x != 0 or cursor_y != 0:
            self.disc_center = QPoint(cursor_x, cursor_y)
        else:
            self.disc_center = QCursor.pos()

        self._setup_window()
        self._setup_animations()

        # Build initial main menu
        self._rebuild_menu_stack()

    def _setup_window(self):
        """Configure full-screen overlay window"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Move window to cover the monitor where the cursor is
        screen = QApplication.screenAt(self.disc_center)
        if screen is None:
            screen = QApplication.primaryScreen()
        self.screen_rect = screen.geometry()
        self.setFixedSize(self.screen_rect.size())
        self.move(self.screen_rect.topLeft())

        self.setMouseTracking(True)
        self.setWindowOpacity(0.0)

    def _setup_animations(self):
        """Set up fade-in animation"""
        self._animation_progress = 0.0
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(150)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        QTimer.singleShot(10, self.anim.start)

    def _rebuild_menu_stack(self):
        """Rebuild the menu stack from config"""
        main_menu = MenuLevel(self.config.items, level=0)
        self.menu_stack = [main_menu]

    def _on_toggle_changed(self, item_id: str, new_state: bool):
        """Callback when a toggle item changes state"""
        # Update the item in the menu structure
        def update_item(items: List[DiscItem]) -> bool:
            for item in items:
                if item.id == item_id:
                    item.toggle_state = new_state
                    return True
                if update_item(item.children):
                    return True
            return False

        update_item(self.config.items)
        self.update()

    def paintEvent(self, event):
        """Draw all menu levels"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.disc_center.x() - self.screen_rect.x()
        cy = self.disc_center.y() - self.screen_rect.y()

        # Draw each menu level
        for menu_level in self.menu_stack:
            self._draw_menu_level(painter, menu_level, cx, cy)

        # Draw center close button
        self._draw_center_close(painter, cx, cy)

    def _draw_menu_level(self, painter: QPainter, menu: MenuLevel, cx: float, cy: float):
        """Draw one level of menu"""
        style = menu.get_style(self.config)
        num_items = len(menu.items)

        if num_items == 0:
            return

        # Calculate angle step
        if menu.level == 0:
            # Main menu: full circle
            angle_per_item = 360 / num_items
            start_angle = -90  # Start from top
        else:
            # Submenu: fan out around parent angle
            angle_per_item = 360 / len(self.menu_stack[0].items) * style.sub_spacing_factor
            total_span = (num_items - 1) * angle_per_item
            start_angle = menu.parent_angle - total_span / 2

        for i, item in enumerate(menu.items):
            angle = start_angle + i * angle_per_item
            if menu.level == 0:
                angle = i * angle_per_item - 90

            # Position
            dot_x = cx + style.spread_radius * math.cos(math.radians(angle))
            dot_y = cy + style.spread_radius * math.sin(math.radians(angle))

            # Determine color based on state
            is_hovered = (i == menu.hovered_index)
            is_toggle_on = item.action_type == "toggle" and item.toggle_state

            if is_toggle_on:
                if is_hovered:
                    color = QColor(self.config.colors.get("toggle_on_hover", "#ff6060"))
                else:
                    color = QColor(self.config.colors.get("toggle_on", "#ff5050"))
            else:
                if is_hovered:
                    color = QColor(self.config.colors.get("hover", "#ffffff"))
                else:
                    color = QColor(item.color)

            # Draw dot
            radius = style.dot_radius + (style.hover_growth if is_hovered else 0)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QPoint(int(dot_x), int(dot_y)), radius, radius)

            # Draw icon
            icon_color = QColor(self.config.colors.get("icon", "#282828"))
            draw_icon(painter, dot_x, dot_y, style.dot_radius * 0.5, item.id, icon_color)

    def _draw_center_close(self, painter: QPainter, cx: float, cy: float):
        """Draw center close button"""
        center_radius = 20
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.config.colors.get("center_close", "#ffffff")))
        painter.drawEllipse(QPoint(int(cx), int(cy)), center_radius, center_radius)

        # Draw X
        painter.setPen(QPen(QColor(0, 0, 0, 200), 2))
        x_size = center_radius * 0.5
        painter.drawLine(int(cx - x_size), int(cy - x_size), int(cx + x_size), int(cy + x_size))
        painter.drawLine(int(cx + x_size), int(cy - x_size), int(cx - x_size), int(cy + x_size))

    def mouseMoveEvent(self, event):
        """Handle mouse movement for hover detection"""
        import math
        pos = event.pos()
        cx = self.disc_center.x() - self.screen_rect.x()
        cy = self.disc_center.y() - self.screen_rect.y()

        # Check center close button
        dx = pos.x() - cx
        dy = pos.y() - cy
        if (dx ** 2 + dy ** 2) ** 0.5 < self.config.settings.get("close_hit_radius", 25):
            self._collapse_all_submenus()
            self.update()
            return

        # Process each menu level from deepest to shallowest
        handled = False
        for menu_idx in range(len(self.menu_stack) - 1, -1, -1):
            menu = self.menu_stack[menu_idx]
            style = menu.get_style(self.config)

            num_items = len(menu.items)
            if num_items == 0:
                continue

            # Calculate positions
            if menu.level == 0:
                angle_per_item = 360 / num_items
                start_angle = -90
            else:
                main_items = len(self.menu_stack[0].items)
                angle_per_item = 360 / main_items * style.sub_spacing_factor
                total_span = (num_items - 1) * angle_per_item
                start_angle = menu.parent_angle - total_span / 2

            for i, item in enumerate(menu.items):
                angle = start_angle + i * angle_per_item
                if menu.level == 0:
                    angle = i * angle_per_item - 90

                dot_x = cx + style.spread_radius * math.cos(math.radians(angle))
                dot_y = cy + style.spread_radius * math.sin(math.radians(angle))

                dx = pos.x() - dot_x
                dy = pos.y() - dot_y
                dist = (dx ** 2 + dy ** 2) ** 0.5

                if dist < style.hit_radius:
                    # Hovering over this item
                    menu.hovered_index = i

                    # If this item has children, expand it
                    if item.children:
                        self._expand_submenu(menu_idx, i, angle, item)
                    else:
                        # Collapse any deeper submenus
                        self._collapse_submenus_below(menu_idx)

                    handled = True
                    break
            else:
                # Not hovering over any item in this menu
                menu.hovered_index = -1

            if handled:
                break

        if not handled:
            # Check if we're in corridor between menu levels
            # If not, collapse submenus
            pass  # Keep submenus open for now (corridor logic can be added)

        self.update()

    def _expand_submenu(self, parent_menu_idx: int, child_idx: int, angle: float, item: DiscItem):
        """Expand a submenu"""
        # Remove any submenus below this level
        while len(self.menu_stack) > parent_menu_idx + 1:
            self.menu_stack.pop()

        # Mark parent as having expanded child
        self.menu_stack[parent_menu_idx].expanded_child = child_idx

        # Add new submenu level
        submenu = MenuLevel(
            items=item.children,
            parent_angle=angle,
            level=parent_menu_idx + 1,
            parent_item=item
        )
        self.menu_stack.append(submenu)

    def _collapse_submenus_below(self, level: int):
        """Collapse all submenus below the given level"""
        while len(self.menu_stack) > level + 1:
            menu = self.menu_stack.pop()
            # Clear expanded_child on parent
            if self.menu_stack:
                self.menu_stack[-1].expanded_child = None

    def _collapse_all_submenus(self):
        """Collapse all submenus, keeping only main menu"""
        self._collapse_submenus_below(0)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def closeEvent(self, event):
        """Release lock when closing"""
        if hasattr(self, 'lock') and self.lock:
            self.lock.release()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse clicks including back/forward buttons"""
        # Mouse back button (button 4) - previous workspace
        if event.button() == Qt.MouseButton.XButton1:
            subprocess.run(["hyprctl", "dispatch", "workspace", "-1"])
            self.close()
            # Reopen after workspace switch
            QTimer.singleShot(150, lambda: subprocess.Popen(
                ["python3", str(Path(__file__).resolve()), "--show"]
            ))
            return

        # Mouse forward button (button 5) - next workspace
        if event.button() == Qt.MouseButton.XButton2:
            subprocess.run(["hyprctl", "dispatch", "workspace", "+1"])
            self.close()
            # Reopen after workspace switch
            QTimer.singleShot(150, lambda: subprocess.Popen(
                ["python3", str(Path(__file__).resolve()), "--show"]
            ))
            return

        # Handle normal clicks
        cx = self.disc_center.x() - self.screen_rect.x()
        cy = self.disc_center.y() - self.screen_rect.y()
        pos = event.pos()

        # Check center close
        dx = pos.x() - cx
        dy = pos.y() - cy
        if (dx ** 2 + dy ** 2) ** 0.5 < self.config.settings.get("close_hit_radius", 25):
            self.close()
            return

        # Check from deepest menu to shallowest
        for menu_idx in range(len(self.menu_stack) - 1, -1, -1):
            menu = self.menu_stack[menu_idx]

            if menu.hovered_index >= 0:
                item = menu.items[menu.hovered_index]

                if item.children:
                    # Menu item - just expand, don't close
                    return
                else:
                    # Action item - execute
                    should_close = self.executor.execute(item)
                    if should_close:
                        self.close()
                    else:
                        self.update()
                    return

        # Clicked outside - close
        self.close()


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
            subprocess.run(["pkill", "-f", "mouse_disc.py --show"])
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
    main()
