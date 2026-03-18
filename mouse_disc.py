#!/usr/bin/env python3
"""
Mouse Disc - A radial menu for Hyprland/Linux
Appears on middle mouse click for quick shortcuts
"""

import sys
import json
import os
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Callable, Optional

from PyQt6.QtWidgets import QApplication, QWidget, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF, pyqtSignal, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QFont, QFontDatabase, QCursor, QIcon, QAction, QShortcut, QKeySequence, QPen


@dataclass
class DiscItem:
    """A single item on the disc"""
    id: str
    label: str
    icon: str
    action: str
    action_type: str  # "command", "app", "hyprland", "media"
    color: str = "#5a5a5a"


class RadialMenu(QWidget):
    """The radial/pie menu widget"""

    def __init__(self, config_path: str = None):
        super().__init__()

        self.config_path = config_path or Path.home() / ".config" / "mouse-disc" / "config.json"
        self.items: List[DiscItem] = []
        self.hovered_index: int = -1
        self.selected_index: int = -1
        self._animation_progress = 0.0

        # Visual settings
        self.inner_radius = 40
        self.outer_radius = 140
        self.gap_degrees = 2
        self.font_size = 11

        # Colors
        self.bg_color = QColor(30, 30, 30, 220)
        self.border_color = QColor(100, 100, 100, 180)
        self.hover_color = QColor(80, 80, 80, 240)
        self.text_color = QColor(255, 255, 255, 255)
        self.accent_colors = [
            "#e06c75", "#98c379", "#e5c07b", "#61afef",
            "#c678dd", "#56b6c2", "#d19a66", "#abb2bf"
        ]

        self._setup_window()
        self._load_config()
        self._setup_animations()
        self._start_workspace_monitor()

        # Sub-menu state (sub_items is set in _load_config)
        self.expanded_index = -1
        self.sub_hovered_index = -1

    def _setup_window(self):
        """Configure full-screen overlay window"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Full screen size - covers entire monitor
        screen = QApplication.primaryScreen()
        self.screen_rect = screen.geometry()
        self.setFixedSize(self.screen_rect.size())

        # Position at top-left of screen
        self.move(self.screen_rect.topLeft())

        # Store cursor position for disc placement
        self.disc_center = QCursor.pos()

        # Enable mouse tracking
        self.setMouseTracking(True)

        # Start fully transparent to hide any window creation artifacts
        self.setWindowOpacity(0.0)

    def _load_config(self):
        """Load configuration from file"""
        default_items = [
            DiscItem("browser", "", "", "firefox", "app", "#e8e8e8"),
            DiscItem("terminal", "", "", "kitty", "app", "#e8e8e8"),
            DiscItem("apps", "", "", "", "menu", "#e8e8e8"),  # Expands to show apps
            DiscItem("editor", "", "", "code", "app", "#e8e8e8"),
            DiscItem("music", "", "", "playerctl play-pause", "command", "#e8e8e8"),
            DiscItem("screenshot", "", "", "grim -g $(slurp) ~/Pictures/$(date +%Y%m%d_%H%M%S).png", "command", "#e8e8e8"),
            DiscItem("lock", "", "", "hyprlock", "command", "#e8e8e8"),
            DiscItem("close_win", "", "", "kill", "hyprland", "#e8e8e8"),
        ]

        # Sub-menu for apps
        self.sub_items = [
            DiscItem("obsidian", "", "", "obsidian", "app", "#e8e8e8"),
            DiscItem("antigravity", "", "", "antigravity", "app", "#e8e8e8"),
            DiscItem("zen", "", "", "zen-browser", "app", "#e8e8e8"),
            DiscItem("zapzap", "", "", "zapzap", "app", "#e8e8e8"),
        ]
        self.expanded_index = -1  # Which item is expanded
        self.sub_hovered_index = -1  # Which sub-item is hovered

        if Path(self.config_path).exists():
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                    self.items = [
                        DiscItem(**item) for item in data.get("items", [])
                    ]
                    # Update visual settings if provided
                    settings = data.get("settings", {})
                    self.inner_radius = settings.get("inner_radius", self.inner_radius)
                    self.outer_radius = settings.get("outer_radius", self.outer_radius)
                    self.font_size = settings.get("font_size", self.font_size)
            except Exception as e:
                print(f"Error loading config: {e}")
                self.items = default_items
        else:
            self.items = default_items
            self._save_default_config()

    def _save_default_config(self):
        """Create default config file"""
        config_dir = Path(self.config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)

        default_config = {
            "items": [
                {"id": "browser", "label": "", "icon": "", "action": "firefox", "action_type": "app", "color": "#e8e8e8"},
                {"id": "terminal", "label": "", "icon": "", "action": "kitty", "action_type": "app", "color": "#e8e8e8"},
                {"id": "apps", "label": "", "icon": "", "action": "", "action_type": "menu", "color": "#e8e8e8"},
                {"id": "editor", "label": "", "icon": "", "action": "code", "action_type": "app", "color": "#e8e8e8"},
                {"id": "music", "label": "", "icon": "", "action": "playerctl play-pause", "action_type": "command", "color": "#e8e8e8"},
                {"id": "screenshot", "label": "", "icon": "", "action": "grim -g $(slurp) ~/Pictures/$(date +%Y%m%d_%H%M%S).png", "action_type": "command", "color": "#e8e8e8"},
                {"id": "lock", "label": "", "icon": "", "action": "hyprlock", "action_type": "command", "color": "#e8e8e8"},
                {"id": "close_win", "label": "", "icon": "", "action": "kill", "action_type": "hyprland", "color": "#e8e8e8"},
            ],
            "settings": {
                "dot_count": 8,
                "spread_distance": 100,
                "dot_radius": 12,
                "animation_duration_ms": 250
            }
        }

        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)

    def _start_workspace_monitor(self):
        """Monitor workspace changes and close when user switches away"""
        self.initial_workspace = self._get_current_workspace()
        print(f"DEBUG: Started on workspace {self.initial_workspace}")

        def check_workspace():
            try:
                current = self._get_current_workspace()
                print(f"DEBUG: current={current}, initial={self.initial_workspace}")
                if current != self.initial_workspace and current != 0:
                    # User switched workspaces via keyboard, close the disc
                    print(f"DEBUG: Workspace changed, closing")
                    self.cleanup_and_close()
                elif self.isVisible():
                    # Check again in 100ms if still visible
                    QTimer.singleShot(100, check_workspace)
            except Exception as e:
                print(f"DEBUG: Error {e}")

        # Start checking
        QTimer.singleShot(100, check_workspace)

    def _get_current_workspace(self):
        """Get current workspace ID"""
        try:
            result = subprocess.run(
                ["hyprctl", "activeworkspace", "-j"],
                capture_output=True,
                text=True,
                timeout=0.1
            )
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                return data.get("id", 0)
        except:
            pass
        return 0

    def _setup_animations(self):
        """Setup open/close animations"""
        self.open_anim = QPropertyAnimation(self, b"animation_progress")
        self.open_anim.setDuration(400)  # Slower to see the spread
        self.open_anim.setStartValue(0.0)
        self.open_anim.setEndValue(1.0)
        self.open_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.open_anim.valueChanged.connect(self.update)

    def showEvent(self, event):
        """Called when window is shown - capture cursor position"""
        # Get cursor position from Hyprland (more reliable in Wayland)
        try:
            result = subprocess.run(
                ["hyprctl", "cursorpos"],
                capture_output=True,
                text=True,
                timeout=0.1
            )
            if result.returncode == 0:
                # Parse "X, Y" output
                coords = result.stdout.strip().split(",")
                x = int(coords[0].strip())
                y = int(coords[1].strip())
                self.disc_center = QPoint(x, y)
            else:
                self.disc_center = QCursor.pos()
        except Exception:
            self.disc_center = QCursor.pos()

        super().showEvent(event)

        # Make window visible after it's fully shown (prevents flash)
        self.setWindowOpacity(1.0)

        # Pin window to all workspaces
        QTimer.singleShot(100, self._pin_window)

        self.animation_progress = 0.0
        self.open_anim.start()

    def _pin_window(self):
        """Pin window to all workspaces using hyprctl"""
        try:
            subprocess.run(
                ["hyprctl", "dispatch", "pin", "class:^(mouse-disc)$"],
                check=False,
                timeout=0.5
            )
        except:
            pass

    def set_animation_progress(self, value):
        self._animation_progress = value

    def get_animation_progress(self):
        return self._animation_progress

    animation_progress = property(get_animation_progress, set_animation_progress)

    def paintEvent(self, event):
        """Draw 6 white dots that spread out from center"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Center position (cursor)
        cx = self.disc_center.x() - self.screen_rect.x()
        cy = self.disc_center.y() - self.screen_rect.y()

        num_items = len(self.items)
        if num_items == 0:
            return

        import math

        # Animation for fade-in
        progress = self._animation_progress
        angle_per_dot = 360 / num_items

        # Fixed spread distance (20% closer to center)
        spread = 112

        # Draw center close button (white circle with X) - no glow
        center_radius = 18

        # Hover effect for center
        if self.hovered_index == -2:  # -2 indicates center is hovered
            center_radius += 4
            center_color = QColor(255, 255, 255, 255)
        else:
            center_color = QColor(255, 255, 255, 220)

        # Draw single center circle (no glow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(center_color)
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(center_radius), int(center_radius))

        # Draw X
        painter.setPen(QColor(0, 0, 0, 200))
        painter.setPen(QPen(QColor(0, 0, 0, 200), 2))
        x_size = center_radius * 0.5
        painter.drawLine(int(cx - x_size), int(cy - x_size), int(cx + x_size), int(cy + x_size))
        painter.drawLine(int(cx + x_size), int(cy - x_size), int(cx - x_size), int(cy + x_size))

        # Draw 6 dots in a circle around center
        for i in range(num_items):
            angle = i * angle_per_dot - 90  # -90 to start from top

            # Fixed dot position in a circle
            dot_x = cx + spread * math.cos(math.radians(angle))
            dot_y = cy + spread * math.sin(math.radians(angle))

            # Always visible dots
            dot_radius = 35

            # Hover effect
            if i == self.hovered_index:
                dot_radius += 5
                color = QColor(255, 255, 255, 255)
                glow = QColor(255, 255, 255, 100)
            else:
                color = QColor(255, 255, 255, 220)
                glow = QColor(255, 255, 255, 60)

            item = self.items[i]
            self._draw_dot(painter, dot_x, dot_y, dot_radius, color, glow,
                          item_id=item.id)

            # If apps menu is expanded, draw sub-items
            if self.expanded_index >= 0 and self.items[self.expanded_index].id == "apps":
                if i == self.expanded_index:
                    self._draw_sub_items(painter, dot_x, dot_y, angle)

    def _draw_dot(self, painter, x, y, radius, color, glow_color, label="", item_id=""):
        """Draw a single dot with custom icon - no glow effect"""
        # Draw single circle (no glow layers)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(
            QPoint(int(x), int(y)),
            int(radius),
            int(radius)
        )

        # Draw icon based on item_id
        icon_color = QColor(40, 40, 40, 220) if color.lightness() > 150 else QColor(255, 255, 255, 220)
        self._draw_icon(painter, x, y, radius * 0.5, item_id, icon_color)

    def _draw_sub_items(self, painter, parent_x, parent_y, parent_angle):
        """Draw sub-menu items arranged on a larger arc at double the distance"""
        import math

        num_sub = len(self.sub_items)
        sub_radius = 35  # Same size as main tabs

        # Sub-items are on a circle at double the distance from center
        main_spread = 112  # Main items radius
        sub_spread = 224   # Double the distance (112 * 2)

        # Use 60% of the angular spacing of main tabs (closer but not overlapping)
        num_main = len(self.items)
        main_angle_step = 360 / num_main
        sub_angle_step = main_angle_step * 0.6  # 60% of main spacing

        # Center the sub-items around the parent angle
        total_span = (num_sub - 1) * sub_angle_step
        start_angle = parent_angle - total_span / 2

        for j in range(num_sub):
            # Calculate angle for this sub-item using reduced step
            sub_angle = start_angle + j * sub_angle_step

            # Position on the larger circle
            sub_x = self.disc_center.x() - self.screen_rect.x() + sub_spread * math.cos(math.radians(sub_angle))
            sub_y = self.disc_center.y() - self.screen_rect.y() + sub_spread * math.sin(math.radians(sub_angle))

            # Hover effect
            if j == self.sub_hovered_index:
                sub_radius_hover = sub_radius + 5  # Same hover effect as main
                color = QColor(255, 255, 255, 255)
            else:
                sub_radius_hover = sub_radius
                color = QColor(232, 232, 232, 220)

            # Draw sub dot
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QPoint(int(sub_x), int(sub_y)), int(sub_radius_hover), int(sub_radius_hover))

            # Draw icon
            icon_color = QColor(40, 40, 40, 220)
            self._draw_icon(painter, sub_x, sub_y, sub_radius * 0.5, self.sub_items[j].id, icon_color)

    def _draw_icon(self, painter, cx, cy, size, item_id, color):
        """Draw a custom icon based on the item type"""
        painter.setPen(QPen(color, max(1.5, size * 0.15)))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if item_id == "browser":
            # Globe icon
            painter.drawEllipse(QPoint(int(cx), int(cy)), int(size * 0.7), int(size * 0.7))
            painter.drawLine(int(cx - size * 0.7), int(cy), int(cx + size * 0.7), int(cy))
            painter.drawLine(int(cx), int(cy - size * 0.7), int(cx), int(cy + size * 0.7))
            # Curved lines
            for offset in [-0.4, 0.4]:
                painter.drawArc(
                    int(cx - size * 0.7), int(cy + offset * size),
                    int(size * 1.4), int(size * 0.8),
                    0, 180 * 16
                )

        elif item_id == "terminal":
            # Terminal window with >_
            rect_size = size * 1.2
            painter.drawRoundedRect(
                int(cx - rect_size/2), int(cy - rect_size/2 * 0.7),
                int(rect_size), int(rect_size * 0.8), 3, 3
            )
            # Prompt symbol
            painter.drawLine(int(cx - size * 0.3), int(cy - size * 0.1), int(cx - size * 0.1), int(cy + size * 0.1))
            painter.drawLine(int(cx - size * 0.1), int(cy + size * 0.1), int(cx + size * 0.2), int(cy - size * 0.2))
            painter.drawLine(int(cx - size * 0.1), int(cy + size * 0.2), int(cx + size * 0.3), int(cy + size * 0.2))

        elif item_id == "files":
            # Folder icon
            folder_w = size * 1.4
            folder_h = size * 1.0
            painter.drawRoundedRect(int(cx - folder_w/2), int(cy - folder_h/2 + size * 0.2), int(folder_w), int(folder_h * 0.7), 2, 2)
            # Folder tab
            painter.drawLine(int(cx - folder_w/2), int(cy - folder_h/2 + size * 0.2),
                           int(cx - folder_w/2 + size * 0.4), int(cy - folder_h/2 + size * 0.2))
            painter.drawLine(int(cx - folder_w/2 + size * 0.4), int(cy - folder_h/2 + size * 0.2),
                           int(cx - folder_w/2 + size * 0.5), int(cy - folder_h/2))
            painter.drawLine(int(cx - folder_w/2 + size * 0.5), int(cy - folder_h/2),
                           int(cx + folder_w/2), int(cy - folder_h/2))

        elif item_id == "editor":
            # Code brackets < />
            painter.drawLine(int(cx - size * 0.4), int(cy - size * 0.3), int(cx - size * 0.6), int(cy))
            painter.drawLine(int(cx - size * 0.6), int(cy), int(cx - size * 0.4), int(cy + size * 0.3))
            painter.drawLine(int(cx + size * 0.4), int(cy - size * 0.3), int(cx + size * 0.6), int(cy))
            painter.drawLine(int(cx + size * 0.6), int(cy), int(cx + size * 0.4), int(cy + size * 0.3))
            painter.drawLine(int(cx - size * 0.1), int(cy - size * 0.4), int(cx + size * 0.1), int(cy + size * 0.4))

        elif item_id == "screenshot":
            # Camera/frame icon
            frame_size = size * 1.2
            painter.drawRect(int(cx - frame_size/2), int(cy - frame_size/2), int(frame_size), int(frame_size))
            # Corner brackets
            corner = size * 0.3
            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                px = cx + dx * frame_size/2
                py = cy + dy * frame_size/2
                painter.drawLine(int(px), int(py - dy * corner), int(px), int(py))
                painter.drawLine(int(px - dx * corner), int(py), int(px), int(py))
            # Center dot
            painter.setBrush(color)
            painter.drawEllipse(QPoint(int(cx), int(cy)), int(size * 0.2), int(size * 0.2))

        elif item_id == "close_win":
            # X icon
            painter.drawLine(int(cx - size * 0.5), int(cy - size * 0.5), int(cx + size * 0.5), int(cy + size * 0.5))
            painter.drawLine(int(cx + size * 0.5), int(cy - size * 0.5), int(cx - size * 0.5), int(cy + size * 0.5))

        elif item_id == "music":
            # Music note icon
            # Note head (circle)
            painter.setBrush(color)
            painter.drawEllipse(QPoint(int(cx - size * 0.2), int(cy + size * 0.3)), int(size * 0.25), int(size * 0.2))
            # Stem
            painter.drawLine(int(cx + size * 0.05), int(cy + size * 0.3), int(cx + size * 0.05), int(cy - size * 0.4))
            # Flag
            painter.drawLine(int(cx + size * 0.05), int(cy - size * 0.4), int(cx + size * 0.4), int(cy - size * 0.1))
            painter.drawLine(int(cx + size * 0.4), int(cy - size * 0.1), int(cx + size * 0.05), int(cy + size * 0.1))

        elif item_id == "lock":
            # Lock icon
            lock_w = size * 0.8
            lock_h = size * 0.6
            # Lock body
            painter.drawRoundedRect(int(cx - lock_w/2), int(cy - lock_h/2 + size * 0.2), int(lock_w), int(lock_h), 3, 3)
            # Shackle (arc)
            painter.drawArc(int(cx - lock_w/2), int(cy - size * 0.6), int(lock_w), int(size * 0.8), 0, 180 * 16)
            # Keyhole
            painter.setBrush(color)
            painter.drawEllipse(QPoint(int(cx), int(cy + size * 0.1)), int(size * 0.1), int(size * 0.1))
            painter.drawLine(int(cx), int(cy + size * 0.1), int(cx), int(cy + size * 0.3))

        elif item_id == "apps":
            # Grid of 4 squares (app launcher icon)
            sq = size * 0.35
            gap = size * 0.1
            for dx in [-1, 1]:
                for dy in [-1, 1]:
                    sx = cx + dx * (sq/2 + gap/2)
                    sy = cy + dy * (sq/2 + gap/2)
                    painter.drawRect(int(sx - sq/2), int(sy - sq/2), int(sq), int(sq))

        elif item_id == "obsidian":
            # Crystal/gem shape
            painter.drawPolygon([
                QPoint(int(cx), int(cy - size * 0.6)),
                QPoint(int(cx + size * 0.5), int(cy - size * 0.2)),
                QPoint(int(cx + size * 0.3), int(cy + size * 0.5)),
                QPoint(int(cx - size * 0.3), int(cy + size * 0.5)),
                QPoint(int(cx - size * 0.5), int(cy - size * 0.2)),
            ])

        elif item_id == "antigravity":
            # Up arrow (anti-gravity)
            painter.drawLine(int(cx), int(cy + size * 0.4), int(cx), int(cy - size * 0.4))
            painter.drawLine(int(cx - size * 0.4), int(cy), int(cx), int(cy - size * 0.4))
            painter.drawLine(int(cx + size * 0.4), int(cy), int(cx), int(cy - size * 0.4))

        elif item_id == "zen":
            # Z letter
            painter.drawLine(int(cx - size * 0.4), int(cy - size * 0.4), int(cx + size * 0.4), int(cy - size * 0.4))
            painter.drawLine(int(cx + size * 0.4), int(cy - size * 0.4), int(cx - size * 0.4), int(cy + size * 0.4))
            painter.drawLine(int(cx - size * 0.4), int(cy + size * 0.4), int(cx + size * 0.4), int(cy + size * 0.4))

        elif item_id == "zapzap":
            # Lightning bolt
            painter.drawPolygon([
                QPoint(int(cx + size * 0.3), int(cy - size * 0.5)),
                QPoint(int(cx - size * 0.1), int(cy)),
                QPoint(int(cx + size * 0.2), int(cy)),
                QPoint(int(cx - size * 0.2), int(cy + size * 0.5)),
                QPoint(int(cx + size * 0.1), int(cy)),
                QPoint(int(cx - size * 0.3), int(cy)),
            ])

    def _create_segment_path(self, cx, cy, inner_r, outer_r, start_angle, end_angle):
        """Create a pie segment path"""
        from PyQt6.QtGui import QPainterPath

        path = QPainterPath()

        # Start from inner arc
        start_rad = start_angle * 3.14159 / 180
        path.moveTo(cx + inner_r * cos_deg(start_angle), cy - inner_r * sin_deg(start_angle))

        # Outer arc
        path.arcTo(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2,
                   start_angle, end_angle - start_angle)

        # Line to inner arc end
        path.lineTo(cx + inner_r * cos_deg(end_angle), cy - inner_r * sin_deg(end_angle))

        # Inner arc (clockwise to close)
        path.arcTo(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2,
                   end_angle, start_angle - end_angle)

        path.closeSubpath()
        return path

    def mouseMoveEvent(self, event):
        """Handle mouse movement for hover effects on dots and center"""
        import math
        pos = event.pos()

        # Center position
        cx = self.disc_center.x() - self.screen_rect.x()
        cy = self.disc_center.y() - self.screen_rect.y()

        # Check if hovering over center close button
        dx = pos.x() - cx
        dy = pos.y() - cy
        dist_to_center = (dx ** 2 + dy ** 2) ** 0.5

        if dist_to_center < 25:
            self.hovered_index = -2  # Special value for center
            self.expanded_index = -1  # Collapse any expanded menu
            self.sub_hovered_index = -1
            self.update()
            return

        # Check distance to each dot
        num_items = len(self.items)
        angle_per_dot = 360 / num_items
        spread = 112

        self.hovered_index = -1
        self.sub_hovered_index = -1

        # First: find which main item is hovered
        hovered_main_index = -1
        for i in range(num_items):
            angle = i * angle_per_dot - 90
            dot_x = cx + spread * math.cos(math.radians(angle))
            dot_y = cy + spread * math.sin(math.radians(angle))

            dx = pos.x() - dot_x
            dy = pos.y() - dot_y
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance < 50:  # Larger hit area for bigger dots
                hovered_main_index = i
                break

        self.hovered_index = hovered_main_index

        # Second: if apps is hovered, expand it
        if hovered_main_index >= 0 and self.items[hovered_main_index].id == "apps":
            self.expanded_index = hovered_main_index

        # Third: check if hovering over sub-items of expanded menu
        if self.expanded_index >= 0:
            num_sub = len(self.sub_items)
            sub_spread = 224  # Double the main spread (same as in _draw_sub_items)

            # Get the parent angle
            expanded_angle = self.expanded_index * angle_per_dot - 90

            # Calculate the arc angles (same as drawing)
            num_main = len(self.items)
            main_angle_step = 360 / num_main
            sub_angle_step = main_angle_step * 0.6  # 60% of main spacing
            total_span = (num_sub - 1) * sub_angle_step
            start_angle = expanded_angle - total_span / 2

            for j in range(num_sub):
                sub_angle = start_angle + j * sub_angle_step
                sub_x = cx + sub_spread * math.cos(math.radians(sub_angle))
                sub_y = cy + sub_spread * math.sin(math.radians(sub_angle))

                dx_sub = pos.x() - sub_x
                dy_sub = pos.y() - sub_y
                dist_sub = (dx_sub ** 2 + dy_sub ** 2) ** 0.5

                if dist_sub < 50:  # Same hit area as main items
                    self.sub_hovered_index = j
                    break

            # If not hovering over sub-items AND not hovering over the parent, collapse
            if self.sub_hovered_index < 0 and hovered_main_index != self.expanded_index:
                parent_x = cx + spread * math.cos(math.radians(expanded_angle))
                parent_y = cy + spread * math.sin(math.radians(expanded_angle))
                dx_parent = pos.x() - parent_x
                dy_parent = pos.y() - parent_y
                dist_parent = (dx_parent ** 2 + dy_parent ** 2) ** 0.5
                if dist_parent > 60:  # Far from parent, collapse
                    self.expanded_index = -1

        # Debug: print state when apps is hovered or expanded
        self.update()

    def mousePressEvent(self, event):
        """Handle click to select item or close"""
        # Mouse back button (button 4) - previous workspace then reopen
        if event.button() == Qt.MouseButton.XButton1:
            subprocess.run(["hyprctl", "dispatch", "workspace", "-1"])
            self.cleanup_and_close()
            # Reopen after workspace switch
            subprocess.Popen(
                ["bash", "-c", "sleep 0.15 && python3 ~/Projects/mouse-disc/mouse_disc.py --show"]
            )
            return

        # Mouse forward button (button 5) - next workspace then reopen
        if event.button() == Qt.MouseButton.XButton2:
            subprocess.run(["hyprctl", "dispatch", "workspace", "+1"])
            self.cleanup_and_close()
            # Reopen after workspace switch
            subprocess.Popen(
                ["bash", "-c", "sleep 0.15 && python3 ~/Projects/mouse-disc/mouse_disc.py --show"]
            )
            return

        # Clicking center (-2) closes without action
        if self.hovered_index == -2:
            self.cleanup_and_close()
            return

        # Check if clicking on a sub-item first
        if self.sub_hovered_index >= 0 and self.expanded_index >= 0:
            self.execute_action(self.sub_items[self.sub_hovered_index])
            self.cleanup_and_close()
            return

        # Clicking outside all items closes it
        if self.hovered_index < 0:
            self.cleanup_and_close()
            return

        # Check if clicking on the apps menu item (which shouldn't execute, just expand)
        if self.items[self.hovered_index].id == "apps":
            # Just expand it, don't close
            self.expanded_index = self.hovered_index
            self.update()
            return

        self.selected_index = self.hovered_index
        self.execute_action(self.items[self.hovered_index])
        self.cleanup_and_close()

    def cleanup_and_close(self):
        """Clean up lock file and close window"""
        lock_file = Path("/tmp/mouse-disc.lock")
        if lock_file.exists():
            try:
                lock_file.unlink()
            except:
                pass
        self.close()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def execute_action(self, item: DiscItem):
        """Execute the action for an item"""
        try:
            if item.action_type == "command":
                subprocess.Popen(item.action, shell=True)
            elif item.action_type == "app":
                subprocess.Popen([item.action])
            elif item.action_type == "hyprland":
                subprocess.run(["hyprctl", item.action])
            elif item.action_type == "media":
                if item.action == "play-pause":
                    subprocess.run(["playerctl", "play-pause"])
                elif item.action == "next":
                    subprocess.run(["playerctl", "next"])
                elif item.action == "previous":
                    subprocess.run(["playerctl", "previous"])
                elif item.action.startswith("volume"):
                    change = item.action.split()[1] if " " in item.action else "5%"
                    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", change])
        except Exception as e:
            print(f"Error executing action: {e}")


def cos_deg(angle):
    import math
    return math.cos(math.radians(angle))


def sin_deg(angle):
    import math
    return math.sin(math.radians(angle))


class MouseDiscApp:
    """Main application class"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("mouse-disc")
        self.app.setQuitOnLastWindowClosed(False)

        # Create tray icon
        self._create_tray()

        # Global hotkey for middle click simulation (optional)
        self.menu = None

    def _create_tray(self):
        """Create system tray icon"""
        from PyQt6.QtWidgets import QSystemTrayIcon, QMenu

        self.tray = QSystemTrayIcon(self.app)
        self.tray.setToolTip("Mouse Disc - Middle click to open")

        # Create tray menu
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
        self.tray.show()

    def _open_config(self):
        """Open config file in editor"""
        config_path = Path.home() / ".config" / "mouse-disc" / "config.json"
        subprocess.Popen(["xdg-open", str(config_path)])

    def show_menu(self):
        """Show the radial menu"""
        if self.menu is not None:
            self.menu.close()
            self.menu.deleteLater()

        self.menu = RadialMenu()
        self.menu.show()
        self.menu.activateWindow()
        self.menu.raise_()

    def run(self):
        """Start the application"""
        print("Mouse Disc started. Middle-click to open the menu.")
        print("Running in system tray.")
        return self.app.exec()


def main():
    # Handle CLI args for Hyprland integration
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        # Check if already running - if so, kill it (toggle behavior)
        lock_file = Path("/tmp/mouse-disc.lock")
        if lock_file.exists():
            try:
                pid = int(lock_file.read_text().strip())
                # Kill the existing instance
                subprocess.run(["kill", "-TERM", str(pid)], check=False)
                lock_file.unlink()
                return 0  # Exit without opening new one
            except:
                pass

        # Show menu and exit (for hotkey binding)
        app = QApplication(sys.argv)

        # Write our PID to lock file
        lock_file.write_text(str(os.getpid()))

        menu = RadialMenu()
        menu.show()

        # Clean up lock file on close
        def on_close():
            if lock_file.exists():
                lock_file.unlink()

        menu.destroyed.connect(on_close)
        app.aboutToQuit.connect(on_close)

        return app.exec()

    app = MouseDiscApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
