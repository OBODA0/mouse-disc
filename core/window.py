"""Mouse Disc main window - refactored to use modular tabs"""
import sys
import math
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QCursor, QFont
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QTimer

from config import ConfigManager, DiscItem, MenuStyle
from core.menu_level import MenuLevel
from core.actions import ActionExecutor
from core.icons import draw_icon
from tabs import get_registry
from tabs.controls import check_brightness_bar_click, apply_brightness


class MouseDiscWindow(QWidget):
    """Main radial menu window"""

    def __init__(self, config_manager: ConfigManager, lock,
                 cursor_x: int = 0, cursor_y: int = 0):
        super().__init__()
        self.config_manager = config_manager
        self.config = config_manager.config
        self.executor = ActionExecutor(self._on_toggle_changed)
        self.lock = lock

        # Tab registry
        self.tab_registry = get_registry()

        # Menu stack: [main, submenu1, submenu2, ...]
        self.menu_stack: List[MenuLevel] = []

        # Brightness level (0.0 to 1.0) for the controls bar
        self.brightness_level = 1.0

        # Track current workspace to detect switches
        self.current_workspace = self._get_current_workspace()
        self.workspace_check_timer = QTimer(self)
        self.workspace_check_timer.timeout.connect(self._check_workspace_switch)

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

        # Start workspace monitoring
        self.workspace_check_timer.start(100)  # Check every 100ms

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
        wifi_tab = self.tab_registry.get("wifi")
        if wifi_tab and wifi_tab.sync_state:
            wifi_tab.toggle_state = wifi_tab.sync_state()
            self._update_toggle_state("wifi", wifi_tab.toggle_state)

        # Check Bluetooth state
        bt_tab = self.tab_registry.get("bluetooth")
        if bt_tab and bt_tab.sync_state:
            bt_tab.toggle_state = bt_tab.sync_state()
            self._update_toggle_state("bluetooth", bt_tab.toggle_state)

        # Check speaker mute state
        speakers_tab = self.tab_registry.get("mute_speakers")
        if speakers_tab and speakers_tab.sync_state:
            speakers_tab.toggle_state = speakers_tab.sync_state()
            self._update_toggle_state("mute_speakers", speakers_tab.toggle_state)

        # Check mic mute state
        mic_tab = self.tab_registry.get("mute_mic")
        if mic_tab and mic_tab.sync_state:
            mic_tab.toggle_state = mic_tab.sync_state()
            self._update_toggle_state("mute_mic", mic_tab.toggle_state)

        # Check brightness state
        try:
            from tabs.controls import get_brightness_state
            self.brightness_level = get_brightness_state()
        except Exception:
            pass

    def _get_current_workspace(self) -> int:
        """Get current workspace ID from Hyprland"""
        try:
            result = subprocess.run(
                ["hyprctl", "activeworkspace"],
                capture_output=True, text=True, timeout=0.5
            )
            if result.returncode == 0:
                # Parse "workspace ID ..." from output
                for line in result.stdout.split('\n'):
                    if line.strip().startswith('workspace ID'):
                        parts = line.split()
                        if len(parts) >= 3:
                            return int(parts[2])
        except Exception:
            pass
        return 0

    def _check_workspace_switch(self):
        """Check if workspace changed and close disc if so"""
        new_workspace = self._get_current_workspace()
        if new_workspace != self.current_workspace:
            # Workspace switched - close the disc
            self.close()
        # Otherwise keep checking

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
        """Rebuild the menu stack from tab registry"""
        items = self.tab_registry.get_all_items()
        main_menu = MenuLevel(items, level=0)
        self.menu_stack = [main_menu]

    def _on_toggle_changed(self, item_id: str, new_state: bool):
        """Callback when a toggle item changes state"""
        # Update the tab
        tab = self.tab_registry.get(item_id)
        if tab:
            tab.toggle_state = new_state

        # Update in config items
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

            # Draw icon - use tab's custom drawer if available, else default
            icon_color = QColor(self.config.colors.get("icon", "#282828"))
            tab = self.tab_registry.get(item.id)
            if tab and tab.icon_drawer:
                tab.icon_drawer(painter, dot_x, dot_y, style.dot_radius * 0.5, icon_color)
            else:
                draw_icon(painter, dot_x, dot_y, style.dot_radius * 0.5, item.id, icon_color)

            # Draw sketch-style label line
            self._draw_label_line(painter, dot_x, dot_y, item.label, angle, is_hovered)

    def _draw_controls_bar(self, painter: QPainter, menu: MenuLevel, cx: float, cy: float,
                           start_angle: float, angle_per_item: float, num_items: int, style):
        """Draw the curved brightness bar"""
        from tabs.controls import draw_brightness_bar

        bar_radius = style.spread_radius * 1.5
        bar_thickness = style.dot_radius * 0.9

        # Calculate actual first and last angles for this submenu
        first_angle = start_angle
        last_angle = start_angle + (num_items - 1) * angle_per_item

        draw_brightness_bar(
            painter, cx, cy, self.brightness_level,
            bar_radius, bar_thickness, self.config.colors,
            first_angle, last_angle
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

    def _draw_label_line(self, painter: QPainter, dot_x: float, dot_y: float, label: str,
                         item_angle: float, is_hovered: bool):
        """Draw a sketch-style label line extending from the tab with the name on top

        Line extends outward from the tab circle center, snapping to nearest
        cardinal angle (0°, 45°, 90°, etc.). Text sits on the line like a note.
        """
        if not label:
            return

        # Normalize angle to 0-360
        norm_angle = item_angle % 360
        if norm_angle < 0:
            norm_angle += 360

        # Snap to nearest cardinal angle: 0, 45, 90, 135, 180, 225, 270, 315
        snapped_angle = round(norm_angle / 45) * 45
        if snapped_angle >= 360:
            snapped_angle = 0

        # Line settings - always white for labels
        line_color = QColor("#ffffff")

        # Setup font for measuring text
        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)

        # Get text dimensions
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(label)
        text_height = metrics.height()

        # Line gap from circle edge
        gap = 8
        line_extension = text_width * 0.6  # Line extends based on text width

        # Calculate line start (from edge of dot, not center)
        dot_radius = 35  # Approximate dot radius
        start_x = dot_x + (dot_radius + gap) * math.cos(math.radians(snapped_angle))
        start_y = dot_y + (dot_radius + gap) * math.sin(math.radians(snapped_angle))

        # Calculate line end - extends outward based on text length
        end_x = start_x + line_extension * math.cos(math.radians(snapped_angle))
        end_y = start_y + line_extension * math.sin(math.radians(snapped_angle))

        # Draw the line
        pen = QPen(line_color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))

        # Draw text positioned on the line
        # Position text so it sits "on top" of the line end
        text_padding = 6

        # Calculate text position based on angle direction
        if snapped_angle == 0:  # Right
            text_x = end_x + text_padding
            text_y = end_y + text_height / 4
        elif snapped_angle == 45:  # Top-right
            text_x = end_x + text_padding
            text_y = end_y - text_height / 2
        elif snapped_angle == 90:  # Top
            text_x = end_x - text_width / 2
            text_y = end_y - text_padding
        elif snapped_angle == 135:  # Top-left
            text_x = end_x - text_width - text_padding
            text_y = end_y - text_height / 2
        elif snapped_angle == 180:  # Left
            text_x = end_x - text_width - text_padding
            text_y = end_y + text_height / 4
        elif snapped_angle == 225:  # Bottom-left
            text_x = end_x - text_width - text_padding
            text_y = end_y + text_height
        elif snapped_angle == 270:  # Bottom
            text_x = end_x - text_width / 2
            text_y = end_y + text_height + text_padding
        else:  # 315 - Bottom-right
            text_x = end_x + text_padding
            text_y = end_y + text_height

        # Draw text with slight offset shadow for depth
        shadow_color = QColor(0, 0, 0, 100)
        painter.setPen(shadow_color)
        painter.drawText(int(text_x + 1), int(text_y + 1), label)

        # Draw main text
        painter.setPen(line_color)
        painter.drawText(int(text_x), int(text_y), label)

    def mouseMoveEvent(self, event):
        """Handle mouse movement for hover detection"""
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
        bar_radius = style.spread_radius * 1.5
        bar_thickness = style.dot_radius * 0.9

        # Calculate actual angles for the controls submenu
        num_items = len(controls_menu.items)
        if num_items == 0:
            return False

        main_items = len(self.menu_stack[0].items)
        angle_per_item = 360 / main_items * style.sub_spacing_factor
        total_span = (num_items - 1) * angle_per_item
        start_angle = controls_menu.parent_angle - total_span / 2
        first_angle = start_angle
        last_angle = start_angle + (num_items - 1) * angle_per_item

        new_brightness = check_brightness_bar_click(
            px, py, cx, cy, bar_radius, bar_thickness,
            first_angle, last_angle
        )
        if new_brightness >= 0:
            self.brightness_level = new_brightness
            return True

        return False

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
        """Release lock and stop timers when closing"""
        # Stop workspace check timer
        if hasattr(self, 'workspace_check_timer') and self.workspace_check_timer:
            self.workspace_check_timer.stop()
        # Release single instance lock
        if hasattr(self, 'lock') and self.lock:
            self.lock.release()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse clicks including back/forward buttons"""
        # Right click - check if on any item first (don't close if on item)
        if event.button() == Qt.MouseButton.RightButton:
            if self._handle_right_click():
                # Handled (clicked on item) - keep menu open
                return
            # Not on any item - close menu
            self.close()
            return

        # Mouse back button (button 4) - previous workspace
        if event.button() == Qt.MouseButton.XButton1:
            # Switch workspace FIRST, then close and reopen to get new cursor position
            subprocess.run(["hyprctl", "dispatch", "workspace", "-1"])
            self.close()
            # Reopen after workspace switch - main.py --show will get fresh cursor position from hyprland
            QTimer.singleShot(150, lambda: subprocess.Popen(
                ["python3", "/home/oboda/Projects/mouse-disc/main.py", "--show"]
            ))
            return

        # Mouse forward button (button 5) - next workspace
        if event.button() == Qt.MouseButton.XButton2:
            # Switch workspace FIRST, then close and reopen to get new cursor position
            subprocess.run(["hyprctl", "dispatch", "workspace", "+1"])
            self.close()
            # Reopen after workspace switch - main.py --show will get fresh cursor position from hyprland
            QTimer.singleShot(150, lambda: subprocess.Popen(
                ["python3", "/home/oboda/Projects/mouse-disc/main.py", "--show"]
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
        brightness_click = self._check_brightness_bar_click(pos.x(), pos.y(), cx, cy)
        if brightness_click:
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
                    should_close = self._execute_item(item)
                    if should_close:
                        self.close()
                    else:
                        self.update()
                    return

        # Clicked outside - close
        self.close()

    def _check_brightness_bar_click(self, px: float, py: float, cx: float, cy: float) -> bool:
        """Check if mouse click is on the brightness bar"""
        # Only check if controls submenu is open
        controls_menu = None
        for menu in self.menu_stack:
            if menu.level > 0 and menu.parent_item and menu.parent_item.id == "controls":
                controls_menu = menu
                break

        if not controls_menu:
            return False

        style = controls_menu.get_style(self.config)
        bar_radius = style.spread_radius * 1.5
        bar_thickness = style.dot_radius * 0.9

        # Calculate actual angles for the controls submenu
        num_items = len(controls_menu.items)
        if num_items == 0:
            return False

        main_items = len(self.menu_stack[0].items)
        angle_per_item = 360 / main_items * style.sub_spacing_factor
        total_span = (num_items - 1) * angle_per_item
        start_angle = controls_menu.parent_angle - total_span / 2
        first_angle = start_angle
        last_angle = start_angle + (num_items - 1) * angle_per_item

        new_brightness = check_brightness_bar_click(
            px, py, cx, cy, bar_radius, bar_thickness,
            first_angle, last_angle
        )
        if new_brightness >= 0:
            self.brightness_level = new_brightness
            return True

        return False

    def _apply_brightness(self):
        """Apply the current brightness level to the system"""
        apply_brightness(self.brightness_level)
        # Keep menu open

    def _handle_right_click(self) -> bool:
        """Handle right-click - returns True if handled (item clicked)"""
        # Get cursor position relative to screen
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        cx = self.disc_center.x() - self.screen_rect.x()
        cy = self.disc_center.y() - self.screen_rect.y()
        px, py = cursor_pos.x(), cursor_pos.y()

        # Check from deepest menu to shallowest
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

                dx = px - dot_x
                dy = py - dot_y
                dist = (dx ** 2 + dy ** 2) ** 0.5

                if dist < style.hit_radius:
                    # Clicked on this item - handle it but DON'T close menu
                    if item.children:
                        # Menu item - expand it on right-click
                        self._expand_submenu(menu_idx, i, angle, item)
                        self.update()
                    else:
                        # Any action item - execute but keep menu open
                        self._execute_item(item)
                        self.update()
                    return True

        # Not on any item
        return False

    def _execute_item(self, item: DiscItem) -> bool:
        """Execute an item's action, using custom handler if available

        Returns True if menu should close, False if it should stay open.
        """
        # Check if tab has custom action handler
        tab = self.tab_registry.get(item.id)
        if tab and tab.action_handler:
            # Use tab's execute method which properly handles return value
            result = tab.execute()
            # Sync DiscItem toggle_state from tab so UI updates immediately
            if item.action_type == "toggle":
                item.toggle_state = tab.toggle_state
            return result

        # Otherwise use default executor
        result = self.executor.execute(item)
        # Sync DiscItem toggle_state from tab so UI updates immediately
        if item.action_type == "toggle" and tab:
            item.toggle_state = tab.toggle_state
        return result
