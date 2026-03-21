"""Mouse Disc main window - refactored to use modular tabs"""
import sys
import math
import random
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

        # Build initial main menu (lightweight)
        self._rebuild_menu_stack()

        # Defer heavy sync operations until after window appears
        QTimer.singleShot(100, self._sync_toggle_states)

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
        self.setWindowOpacity(0.0)  # Start invisible
        self.hide()  # Don't show until animations are ready

    def _setup_animations(self):
        """Set up fade-in and staggered circle animation"""
        self._animation_progress = 0.0
        self._item_progress = []  # Animation progress for each item (0.0 to 1.0)
        self._item_anim_started = False
        self._item_anim_timer = None

        # Get item count for initial progress array
        items = self.tab_registry.get_all_items()
        self._item_progress = [0.0] * len(items)

        # Window fade-in (quicker)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(50)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Start item animation after window appears
        self.anim.finished.connect(self._start_item_animation)

        # Show window and start animation immediately
        self.show()
        self.anim.start()

    def _start_item_animation(self):
        """Start staggered animation for main menu items from random starting angle"""
        if not self.menu_stack or not self.menu_stack[0].items:
            return

        num_items = len(self.menu_stack[0].items)
        self._item_progress = [0.0] * num_items

        # Separate line animation progress for each item (slower)
        self._line_progress = [0.0] * num_items
        self._line_anim_started = [False] * num_items

        # Randomize starting position for animation
        self._anim_start_offset = random.randint(0, num_items - 1)

        # Animation timing: SLOW for debugging - reveal each item every ~500ms
        self._current_animating_item = 0
        self._item_anim_timer = QTimer(self)
        self._item_anim_timer.timeout.connect(self._animate_items_step)
        self._item_anim_timer.start(50)  # 20fps, slow enough to see

        # Item reveal delay (ms between starting each item)
        self._item_reveal_delay = 500
        self._item_reveal_timer = 0

    def _animate_items_step(self):
        """Update animation progress for all items"""
        if not self.menu_stack or not self.menu_stack[0].items:
            self._item_anim_timer.stop()
            return

        num_items = len(self.menu_stack[0].items)
        all_done = True
        dot_progress_speed = 0.05  # Dot animation speed
        line_progress_speed = 0.02  # Line animation speed (slower)

        for i in range(num_items):
            if i > self._current_animating_item:
                # Haven't started this item yet
                all_done = False
                continue

            # Animate dot appearance
            if self._item_progress[i] < 1.0:
                self._item_progress[i] = min(1.0, self._item_progress[i] + dot_progress_speed)
                all_done = False

            # Start line animation once dot is visible enough
            if self._item_progress[i] > 0.3 and not self._line_anim_started[i]:
                self._line_anim_started[i] = True

            # Animate line extension (slower, continues after dot is done)
            if self._line_anim_started[i] and self._line_progress[i] < 1.0:
                self._line_progress[i] = min(1.0, self._line_progress[i] + line_progress_speed)
                all_done = False

        # Check if we should start the next item
        self._item_reveal_timer += 50
        if (self._current_animating_item < num_items - 1 and
            self._item_reveal_timer >= self._item_reveal_delay):
            self._current_animating_item += 1
            self._item_reveal_timer = 0

        self.update()

        if all_done:
            self._item_anim_timer.stop()

    def _ease_out_elastic(self, t: float) -> float:
        """Elastic ease-out for pop effect"""
        if t >= 1.0:
            return 1.0
        # Elastic overshoot
        c4 = (2 * math.pi) / 3
        return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

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

        # First pass: draw all circles and their labels (synced animation)
        for menu_level in self.menu_stack:
            # Draw labels with dots for main menu (level 0) to sync animation
            draw_labels = (menu_level.level == 0)
            self._draw_menu_level(painter, menu_level, cx, cy, draw_labels=draw_labels)

        # Draw center close button
        self._draw_center_close(painter, cx, cy)

        # Second pass: draw labels only for submenu levels (deepest menu)
        if self.menu_stack:
            deepest_menu = self.menu_stack[-1]
            if deepest_menu.level > 0:
                self._draw_menu_labels(painter, deepest_menu, cx, cy)

    def _draw_menu_level(self, painter: QPainter, menu: MenuLevel, cx: float, cy: float, draw_labels: bool = True):
        """Draw one level of menu - circles and optionally labels"""
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

            # Animation scale for main menu items (reveal from random start position)
            anim_scale = 1.0
            if menu.level == 0 and hasattr(self, '_anim_start_offset'):
                # Map item index to animation progress with random offset
                num_items = len(menu.items)
                anim_index = (i + self._anim_start_offset) % num_items
                if anim_index < len(self._item_progress):
                    # Use easing for pop effect
                    progress = self._item_progress[anim_index]
                    # Elastic pop: overshoot then settle
                    if progress < 1.0:
                        anim_scale = self._ease_out_elastic(progress)
            elif menu.level == 0 and i < len(self._item_progress):
                # Fallback: clockwise reveal
                progress = self._item_progress[i]
                if progress < 1.0:
                    anim_scale = self._ease_out_elastic(progress)

            # Position
            dot_x = cx + style.spread_radius * math.cos(math.radians(angle))
            dot_y = cy + style.spread_radius * math.sin(math.radians(angle))

            # Skip drawing if not yet animated (for clean reveal)
            if anim_scale <= 0.01:
                continue

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

            # Draw dot with animation scale
            base_radius = style.dot_radius + (style.hover_growth if is_hovered else 0)
            radius = int(base_radius * anim_scale)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QPoint(int(dot_x), int(dot_y)), radius, radius)

            # Draw icon with animation scale
            icon_color = QColor(self.config.colors.get("icon", "#282828"))
            icon_size = style.dot_radius * 0.5 * anim_scale
            tab = self.tab_registry.get(item.id)
            if tab and tab.icon_drawer:
                tab.icon_drawer(painter, dot_x, dot_y, icon_size, icon_color)
            else:
                draw_icon(painter, dot_x, dot_y, icon_size, item.id, icon_color)

            # Draw label line with its own slower animation
            if draw_labels:
                # Use separate line progress if available, otherwise fall back to dot scale
                line_anim = self._line_progress[anim_index] if hasattr(self, '_line_progress') and anim_index < len(self._line_progress) else anim_scale
                if line_anim > 0.01:
                    self._draw_label_line(painter, dot_x, dot_y, item.label, angle, is_hovered, line_anim)

    def _draw_menu_labels(self, painter: QPainter, menu: MenuLevel, cx: float, cy: float):
        """Draw labels for a menu level (always shown, no animation delay)"""
        style = menu.get_style(self.config)
        num_items = len(menu.items)

        if num_items == 0:
            return

        # Calculate angle step
        main_items = len(self.menu_stack[0].items)
        if menu.level == 0:
            angle_per_item = 360 / num_items
            start_angle = -90
        else:
            angle_per_item = 360 / main_items * style.sub_spacing_factor
            total_span = (num_items - 1) * angle_per_item
            start_angle = menu.parent_angle - total_span / 2

        for i, item in enumerate(menu.items):
            angle = start_angle + i * angle_per_item
            if menu.level == 0:
                angle = i * angle_per_item - 90

            # Position
            dot_x = cx + style.spread_radius * math.cos(math.radians(angle))
            dot_y = cy + style.spread_radius * math.sin(math.radians(angle))

            # Get label from item or tab
            label = item.label
            if not label:
                tab = self.tab_registry.get(item.id)
                if tab:
                    label = tab.label

            # Always draw labels for deepest menu
            is_hovered = (i == menu.hovered_index)
            self._draw_label_line(painter, dot_x, dot_y, label, angle, is_hovered, 1.0)

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
                         item_angle: float, is_hovered: bool, anim_scale: float = 1.0):
        """Draw an elbow-joint label line: exits at item angle, then bends to cardinal direction

        Line animates from dot center outward, synced with item animation.
        For example: editor (top-right at 45°) -> line exits at 45°, bends to 0° (horizontal),
        label sits on the horizontal part.
        """
        if not label:
            return

        # Normalize angle to 0-360
        norm_angle = item_angle % 360
        if norm_angle < 0:
            norm_angle += 360

        # Map angle ranges to elbow joint directions (Qt coordinate system)
        # Qt: 0=right, 90=down, 180=left, 270=up
        # Use actual angle (not rounded) to determine quadrant
        # Special case: exactly 0° (right) -> up-right to avoid ambiguity
        if norm_angle == 0:
            exit_angle = 315            # Up-right
            line_angle = 0              # Right
        elif 0 < norm_angle <= 180:     # Bottom half -> exit down
            if norm_angle < 90:         # Bottom-right (0-90)
                exit_angle = 45         # Down-right
                line_angle = 0          # Right
            else:                       # Bottom-left (90-180)
                exit_angle = 135        # Down-left
                line_angle = 180        # Left
        else:                           # Top half -> exit up
            if norm_angle < 270:        # Top-left (180-270)
                exit_angle = 225        # Up-left
                line_angle = 180        # Left
            else:                       # Top-right (270-360)
                exit_angle = 315        # Up-right
                line_angle = 0          # Right

        # Line settings - always white
        line_color = QColor("#ffffff")
        pen = QPen(line_color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        # Setup font for measuring text
        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)

        # Get text dimensions
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(label)
        text_height = metrics.height()

        # Gap from circle edge
        gap = 8
        elbow_length = 25  # Length of first segment before bend

        # Animation: line grows from dot center outward based on anim_scale
        # anim_scale goes 0->1 as item appears
        anim = max(0.0, min(1.0, anim_scale))

        # Calculate full line geometry (fixed positions)
        dot_radius = 35

        # Point where line exits the dot (fixed start point)
        start_x = dot_x + (dot_radius + gap) * math.cos(math.radians(exit_angle))
        start_y = dot_y + (dot_radius + gap) * math.sin(math.radians(exit_angle))

        # Elbow point (where the bend happens)
        elbow_x = start_x + elbow_length * math.cos(math.radians(exit_angle))
        elbow_y = start_y + elbow_length * math.sin(math.radians(exit_angle))

        # End point (extend based on text length from elbow)
        line_extension = text_width + 10  # Text width plus some padding
        end_x = elbow_x + line_extension * math.cos(math.radians(line_angle))
        end_y = elbow_y + line_extension * math.sin(math.radians(line_angle))

        # Animate line growing from dot edge outward
        # Two-phase animation: first angled segment, then horizontal segment
        if anim > 0.01:
            # Calculate where the elbow is along the total path
            total_length = elbow_length + line_extension
            elbow_progress = elbow_length / total_length

            if anim <= elbow_progress:
                # Phase 1: Growing angled segment toward elbow
                # anim goes 0->elbow_progress, map to 0->1 for first segment
                segment_progress = anim / elbow_progress
                curr_x = start_x + (elbow_x - start_x) * segment_progress
                curr_y = start_y + (elbow_y - start_y) * segment_progress
                painter.drawLine(int(start_x), int(start_y), int(curr_x), int(curr_y))
            else:
                # Phase 2: Angled segment complete, growing horizontal segment
                # Draw complete first segment
                painter.drawLine(int(start_x), int(start_y), int(elbow_x), int(elbow_y))
                # anim goes elbow_progress->1, map to 0->1 for second segment
                second_progress = (anim - elbow_progress) / (1 - elbow_progress)
                curr_x = elbow_x + (end_x - elbow_x) * second_progress
                curr_y = elbow_y + (end_y - elbow_y) * second_progress
                painter.drawLine(int(elbow_x), int(elbow_y), int(curr_x), int(curr_y))

        # Only draw text when animation is nearly complete
        if anim > 0.7:
            # Draw label on the horizontal/vertical line (the straight part)
            text_padding = 6

            # Position text based on line_angle (at final position)
            if line_angle == 0:  # Horizontal right
                text_x = elbow_x + line_extension / 2 - text_width / 2
                text_y = elbow_y - text_padding
            elif line_angle == 90:  # Vertical up
                text_x = elbow_x - text_width / 2
                text_y = elbow_y - line_extension / 2 - text_height / 2
            elif line_angle == 180:  # Horizontal left
                text_x = elbow_x - line_extension / 2 - text_width / 2
                text_y = elbow_y - text_padding
            else:  # line_angle == 270, vertical down
                text_x = elbow_x - text_width / 2
                text_y = elbow_y + line_extension / 2 + text_height / 2

            # Draw text with slight shadow for depth
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
