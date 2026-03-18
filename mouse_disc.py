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

        # Brightness level (0.0 to 1.0) for the controls bar
        self.brightness_level = 1.0

        # Use provided cursor position (from hyprland) or try to get from Qt
        if cursor_x != 0 or cursor_y != 0:
            self.disc_center = QPoint(cursor_x, cursor_y)
        else:
            self.disc_center = QCursor.pos()

        self._setup_window()
        self._setup_animations()

        # Sync toggle states with actual system state
        self._sync_toggle_states()

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

    def _sync_toggle_states(self):
        """Check actual system state for toggles and update config"""
        # Check WiFi state
        try:
            result = subprocess.run(
                ["nmcli", "radio", "wifi"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                # Output is "enabled" or "disabled"
                wifi_enabled = "enabled" in result.stdout.lower()
                self._update_toggle_state("wifi", wifi_enabled)
        except Exception:
            pass

        # Check Bluetooth state
        try:
            result = subprocess.run(
                ["bluetoothctl", "show"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                # Look for "Powered: yes" in output
                bt_enabled = "powered: yes" in result.stdout.lower()
                self._update_toggle_state("bluetooth", bt_enabled)
        except Exception:
            pass

        # Check speaker mute state for DEFAULT sink
        try:
            # Get default sink name
            default_sink = subprocess.run(
                ["pactl", "info"],
                capture_output=True,
                text=True,
                timeout=1
            )
            sink_name = None
            if default_sink.returncode == 0:
                for line in default_sink.stdout.split('\n'):
                    if 'default sink:' in line.lower():
                        sink_name = line.split(':')[1].strip()
                        break

            # Get mute state for that specific sink
            if sink_name:
                result = subprocess.run(
                    ["pactl", "list", "sinks"],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    in_default_sink = False
                    for line in result.stdout.split('\n'):
                        if f'Name: {sink_name}' in line:
                            in_default_sink = True
                        elif in_default_sink and line.strip().startswith('Name:'):
                            in_default_sink = False
                        if in_default_sink and 'Mute:' in line:
                            # "Mute: no" = unmuted = red = True
                            speakers_unmuted = 'no' in line.lower()
                            self._update_toggle_state("mute_speakers", speakers_unmuted)
                            break
        except Exception:
            pass

        # Check mic mute state for DEFAULT source
        try:
            # Get default source name
            default_source = subprocess.run(
                ["pactl", "info"],
                capture_output=True,
                text=True,
                timeout=1
            )
            source_name = None
            if default_source.returncode == 0:
                for line in default_source.stdout.split('\n'):
                    if 'default source:' in line.lower():
                        source_name = line.split(':')[1].strip()
                        break

            # Get mute state for that specific source
            if source_name:
                result = subprocess.run(
                    ["pactl", "list", "sources"],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    in_default_source = False
                    for line in result.stdout.split('\n'):
                        if f'Name: {source_name}' in line:
                            in_default_source = True
                        elif in_default_source and line.strip().startswith('Name:'):
                            in_default_source = False
                        if in_default_source and 'Mute:' in line:
                            mic_unmuted = 'no' in line.lower()
                            self._update_toggle_state("mute_mic", mic_unmuted)
                            break
        except Exception:
            pass

        # Check brightness state
        try:
            result = subprocess.run(
                ["brightnessctl", "get"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                current = int(result.stdout.strip())
                # Get max brightness
                max_result = subprocess.run(
                    ["brightnessctl", "max"],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if max_result.returncode == 0:
                    max_val = int(max_result.stdout.strip())
                    self.brightness_level = current / max_val
        except Exception:
            pass

    def _update_toggle_state(self, item_id: str, state: bool):
        """Update toggle state in config items"""
        def update_in_items(items):
            for item in items:
                if item.id == item_id:
                    item.toggle_state = state
                    return True
                if item.children:
                    if update_in_items(item.children):
                        return True
            return False

        update_in_items(self.config.items)

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

        # Draw curved bar for controls submenu
        if menu.level > 0 and menu.parent_item and menu.parent_item.id == "controls":
            self._draw_controls_bar(painter, menu, cx, cy, start_angle, angle_per_item, num_items, style)

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

    def _draw_controls_bar(self, painter: QPainter, menu: MenuLevel, cx: float, cy: float,
                           start_angle: float, angle_per_item: float, num_items: int, style):
        """Draw a curved brightness bar hugging the controls submenu items (outside the buttons)"""
        # Bar at 150% of submenu distance from center (outside the buttons)
        bar_radius = style.spread_radius * 1.5

        # Calculate angles for first and last item (in my angle system: 0=right, positive=clockwise)
        first_angle = start_angle
        last_angle = start_angle + (num_items - 1) * angle_per_item

        # Qt system: 0=right, positive=counter-clockwise
        qt_start_angle = -last_angle
        qt_end_angle = -first_angle
        qt_span = qt_end_angle - qt_start_angle

        # Draw the curved bar as a thick arc
        bar_thickness = style.dot_radius * 0.9
        empty_color = QColor(self.config.colors.get("controls_bar_empty", "#3a3a3a"))
        fill_color = QColor(self.config.colors.get("controls_bar_fill", "#ffffff"))

        rect_size = bar_radius * 2

        # Calculate brightness span (fills from bottom upward)
        # At 0% brightness: all dark gray (bottom)
        # At 100% brightness: all white (top)
        brightness_span = qt_span * self.brightness_level
        empty_span = qt_span - brightness_span

        # Draw empty portion (dark gray, from bottom/qt_start_angle upward)
        if empty_span > 0:
            pen = QPen(empty_color, bar_thickness)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(
                int(cx - bar_radius), int(cy - bar_radius),
                int(rect_size), int(rect_size),
                int(qt_start_angle * 16), int(empty_span * 16)
            )

        # Draw filled portion (white, from end of empty to top)
        if brightness_span > 0:
            pen = QPen(fill_color, bar_thickness)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(
                int(cx - bar_radius), int(cy - bar_radius),
                int(rect_size), int(rect_size),
                int((qt_start_angle + empty_span) * 16), int(brightness_span * 16)
            )

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
            # Check if hovering over controls brightness bar
            brightness_hover = self._check_brightness_bar_hover(pos.x(), pos.y(), cx, cy)
            if brightness_hover:
                self.update()
                return

        self.update()

    def _check_brightness_bar_hover(self, px: float, py: float, cx: float, cy: float) -> bool:
        """Check if mouse is over the controls brightness bar and update brightness level"""
        # Only check if controls submenu is open
        controls_menu = None
        for menu in self.menu_stack:
            if menu.level > 0 and menu.parent_item and menu.parent_item.id == "controls":
                controls_menu = menu
                break

        if not controls_menu:
            return False

        style = controls_menu.get_style(self.config)
        num_items = len(controls_menu.items)
        if num_items == 0:
            return False

        # Calculate bar geometry
        bar_radius = style.spread_radius * 1.5
        bar_thickness = style.dot_radius * 0.9

        # Calculate angles
        main_items = len(self.menu_stack[0].items)
        angle_per_item = 360 / main_items * style.sub_spacing_factor
        total_span = (num_items - 1) * angle_per_item
        start_angle = controls_menu.parent_angle - total_span / 2
        first_angle = start_angle
        last_angle = start_angle + (num_items - 1) * angle_per_item

        # Check if mouse is near the bar radius
        dx = px - cx
        dy = py - cy
        dist_from_center = (dx ** 2 + dy ** 2) ** 0.5

        # Mouse angle (in my coordinate system: 0=right, clockwise)
        mouse_angle = math.degrees(math.atan2(dy, dx))
        if mouse_angle < 0:
            mouse_angle += 360

        # Check if within bar thickness
        if abs(dist_from_center - bar_radius) > bar_thickness * 0.6:
            return False

        # Check if within angle range (with some padding)
        angle_padding = 10  # degrees
        # Normalize angles to 0-360 for comparison
        def normalize_angle(a):
            while a < 0:
                a += 360
            while a >= 360:
                a -= 360
            return a

        norm_first = normalize_angle(first_angle)
        norm_last = normalize_angle(last_angle)
        norm_mouse = normalize_angle(mouse_angle)

        # Check if mouse is within the arc range
        if norm_first <= norm_last:
            in_range = norm_first - angle_padding <= norm_mouse <= norm_last + angle_padding
        else:
            # Arc crosses 0/360 boundary
            in_range = (norm_mouse >= norm_first - angle_padding or
                       norm_mouse <= norm_last + angle_padding)

        if not in_range:
            return False

        # Calculate brightness based on position along the arc
        # White fills from bottom to top
        # Bottom (first_angle/wifi) = 0% brightness
        # Top (last_angle/mute_mic) = 100% brightness
        if norm_first <= norm_last:
            if norm_first <= norm_mouse <= norm_last:
                # 0.0 at first (bottom/wifi), 1.0 at last (top/mute_mic)
                self.brightness_level = (norm_mouse - norm_first) / (norm_last - norm_first)
            else:
                if norm_mouse < norm_first:
                    self.brightness_level = 0.0
                else:
                    self.brightness_level = 1.0
        else:
            # Crosses boundary
            if norm_mouse >= norm_first:
                self.brightness_level = (norm_mouse - norm_first) / (norm_last + 360 - norm_first)
            elif norm_mouse <= norm_last:
                self.brightness_level = (norm_mouse + 360 - norm_first) / (norm_last + 360 - norm_first)
            else:
                self.brightness_level = 0.5

        # Clamp to valid range
        self.brightness_level = max(0.0, min(1.0, self.brightness_level))
        return True

    def _check_brightness_bar_click(self, px: float, py: float, cx: float, cy: float) -> bool:
        """Check if mouse click is on the brightness bar (for setting brightness)"""
        # Use the same logic as hover detection
        return self._check_brightness_bar_hover(px, py, cx, cy)

    def _apply_brightness(self):
        """Apply the current brightness level to the system"""
        try:
            brightness_percent = int(self.brightness_level * 100)
            subprocess.run(["brightnessctl", "set", f"{brightness_percent}%"], check=False)
        except Exception as e:
            print(f"Error setting brightness: {e}")
        # Keep menu open

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
        # Right click - close menu without action (anywhere)
        if event.button() == Qt.MouseButton.RightButton:
            self.close()
            return

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

        # Check if clicked on brightness bar to apply brightness
        if self._check_brightness_bar_click(pos.x(), pos.y(), cx, cy):
            self._apply_brightness()
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
