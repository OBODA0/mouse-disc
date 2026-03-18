"""Icon drawing functions for Mouse Disc"""
import math
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt, QPoint


def draw_icon(painter: QPainter, cx: float, cy: float, size: float, item_id: str, color: QColor):
    """Draw a custom icon based on the item type"""
    painter.setPen(QPen(color, max(1.5, size * 0.15)))
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Map of icon drawers
    icon_drawers = {
        "browser": _draw_browser,
        "terminal": _draw_terminal,
        "editor": _draw_editor,
        "screenshot": _draw_screenshot,
        "close_win": _draw_close,
        "music": _draw_music,
        "lock": _draw_lock,
        "apps": _draw_apps,
        "controls": _draw_controls,
        "obsidian": _draw_obsidian,
        "antigravity": _draw_antigravity,
        "zen": _draw_zen,
        "zapzap": _draw_zapzap,
        "wifi": _draw_wifi,
        "bluetooth": _draw_bluetooth,
        "mute_speakers": _draw_mute_speakers,
        "mute_mic": _draw_mute_mic,
        "brightness": _draw_brightness,
    }

    drawer = icon_drawers.get(item_id, _draw_unknown)
    drawer(painter, cx, cy, size, color)


def _draw_browser(painter, cx, cy, size, color):
    # Globe icon
    painter.drawEllipse(QPoint(int(cx), int(cy)), int(size * 0.5), int(size * 0.5))
    painter.drawLine(int(cx), int(cy - size * 0.5), int(cx), int(cy + size * 0.5))
    painter.drawLine(int(cx - size * 0.5), int(cy), int(cx + size * 0.5), int(cy))
    painter.drawArc(int(cx - size * 0.5), int(cy - size * 0.25), int(size), int(size * 0.5), 0, 180 * 16)
    painter.drawArc(int(cx - size * 0.5), int(cy - size * 0.25), int(size), int(size * 0.5), 0, -180 * 16)


def _draw_terminal(painter, cx, cy, size, color):
    # Terminal prompt icon
    painter.drawRoundedRect(int(cx - size * 0.55), int(cy - size * 0.4), int(size * 1.1), int(size * 0.8), 4, 4)
    painter.drawText(int(cx - size * 0.35), int(cy + size * 0.15), ">_")


def _draw_editor(painter, cx, cy, size, color):
    # Code brackets < />
    painter.drawLine(int(cx - size * 0.4), int(cy - size * 0.3), int(cx - size * 0.6), int(cy))
    painter.drawLine(int(cx - size * 0.6), int(cy), int(cx - size * 0.4), int(cy + size * 0.3))
    painter.drawLine(int(cx + size * 0.4), int(cy - size * 0.3), int(cx + size * 0.6), int(cy))
    painter.drawLine(int(cx + size * 0.6), int(cy), int(cx + size * 0.4), int(cy + size * 0.3))
    painter.drawLine(int(cx - size * 0.1), int(cy - size * 0.4), int(cx + size * 0.1), int(cy + size * 0.4))


def _draw_screenshot(painter, cx, cy, size, color):
    frame_size = size * 1.2
    painter.drawRect(int(cx - frame_size/2), int(cy - frame_size/2), int(frame_size), int(frame_size))
    corner = size * 0.3
    for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        px = cx + dx * frame_size/2
        py = cy + dy * frame_size/2
        painter.drawLine(int(px), int(py - dy * corner), int(px), int(py))
        painter.drawLine(int(px - dx * corner), int(py), int(px), int(py))
    painter.setBrush(color)
    painter.drawEllipse(QPoint(int(cx), int(cy)), int(size * 0.2), int(size * 0.2))


def _draw_close(painter, cx, cy, size, color):
    painter.drawLine(int(cx - size * 0.5), int(cy - size * 0.5), int(cx + size * 0.5), int(cy + size * 0.5))
    painter.drawLine(int(cx + size * 0.5), int(cy - size * 0.5), int(cx - size * 0.5), int(cy + size * 0.5))


def _draw_music(painter, cx, cy, size, color):
    painter.setBrush(color)
    painter.drawEllipse(QPoint(int(cx - size * 0.2), int(cy + size * 0.3)), int(size * 0.25), int(size * 0.2))
    painter.drawLine(int(cx + size * 0.05), int(cy + size * 0.3), int(cx + size * 0.05), int(cy - size * 0.4))
    painter.drawLine(int(cx + size * 0.05), int(cy - size * 0.4), int(cx + size * 0.4), int(cy - size * 0.1))
    painter.drawLine(int(cx + size * 0.4), int(cy - size * 0.1), int(cx + size * 0.05), int(cy + size * 0.1))


def _draw_lock(painter, cx, cy, size, color):
    lock_w = size * 0.8
    lock_h = size * 0.6
    painter.drawRoundedRect(int(cx - lock_w/2), int(cy - lock_h/2 + size * 0.2), int(lock_w), int(lock_h), 3, 3)
    painter.drawArc(int(cx - lock_w/2), int(cy - size * 0.6), int(lock_w), int(size * 0.8), 0, 180 * 16)
    painter.setBrush(color)
    painter.drawEllipse(QPoint(int(cx), int(cy + size * 0.1)), int(size * 0.1), int(size * 0.1))
    painter.drawLine(int(cx), int(cy + size * 0.1), int(cx), int(cy + size * 0.3))


def _draw_apps(painter, cx, cy, size, color):
    sq = size * 0.35
    gap = size * 0.1
    for dx in [-1, 1]:
        for dy in [-1, 1]:
            sx = cx + dx * (sq/2 + gap/2)
            sy = cy + dy * (sq/2 + gap/2)
            painter.drawRect(int(sx - sq/2), int(sy - sq/2), int(sq), int(sq))


def _draw_controls(painter, cx, cy, size, color):
    for sx in [cx - size * 0.25, cx + size * 0.25]:
        painter.drawLine(int(sx), int(cy - size * 0.4), int(sx), int(cy + size * 0.4))
        knob_y = cy + (0.2 if sx < cx else -0.2) * size
        painter.drawRect(int(sx - size * 0.1), int(knob_y - size * 0.08), int(size * 0.2), int(size * 0.16))


def _draw_obsidian(painter, cx, cy, size, color):
    painter.drawPolygon([
        QPoint(int(cx), int(cy - size * 0.6)),
        QPoint(int(cx + size * 0.5), int(cy - size * 0.2)),
        QPoint(int(cx + size * 0.3), int(cy + size * 0.5)),
        QPoint(int(cx - size * 0.3), int(cy + size * 0.5)),
        QPoint(int(cx - size * 0.5), int(cy - size * 0.2)),
    ])


def _draw_antigravity(painter, cx, cy, size, color):
    painter.drawLine(int(cx), int(cy + size * 0.4), int(cx), int(cy - size * 0.4))
    painter.drawLine(int(cx - size * 0.4), int(cy), int(cx), int(cy - size * 0.4))
    painter.drawLine(int(cx + size * 0.4), int(cy), int(cx), int(cy - size * 0.4))


def _draw_zen(painter, cx, cy, size, color):
    painter.drawLine(int(cx - size * 0.4), int(cy - size * 0.4), int(cx + size * 0.4), int(cy - size * 0.4))
    painter.drawLine(int(cx + size * 0.4), int(cy - size * 0.4), int(cx - size * 0.4), int(cy + size * 0.4))
    painter.drawLine(int(cx - size * 0.4), int(cy + size * 0.4), int(cx + size * 0.4), int(cy + size * 0.4))


def _draw_zapzap(painter, cx, cy, size, color):
    painter.drawPolygon([
        QPoint(int(cx + size * 0.3), int(cy - size * 0.5)),
        QPoint(int(cx - size * 0.1), int(cy)),
        QPoint(int(cx + size * 0.2), int(cy)),
        QPoint(int(cx - size * 0.2), int(cy + size * 0.5)),
        QPoint(int(cx + size * 0.1), int(cy)),
        QPoint(int(cx - size * 0.4), int(cy)),
    ])


def _draw_wifi(painter, cx, cy, size, color):
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for i, r in enumerate([0.2, 0.4, 0.6]):
        painter.drawArc(int(cx - size * r), int(cy - size * r), int(size * r * 2), int(size * r * 2), 45 * 16, 90 * 16)
    painter.setBrush(color)
    painter.drawEllipse(QPoint(int(cx), int(cy + size * 0.65)), int(size * 0.12), int(size * 0.12))


def _draw_bluetooth(painter, cx, cy, size, color):
    painter.drawLine(int(cx), int(cy - size * 0.5), int(cx), int(cy + size * 0.5))
    painter.drawLine(int(cx - size * 0.3), int(cy - size * 0.25), int(cx), int(cy))
    painter.drawLine(int(cx - size * 0.3), int(cy + size * 0.25), int(cx), int(cy))
    painter.drawLine(int(cx), int(cy), int(cx + size * 0.3), int(cy - size * 0.25))
    painter.drawLine(int(cx), int(cy), int(cx + size * 0.3), int(cy + size * 0.25))


def _draw_mute_speakers(painter, cx, cy, size, color):
    # Speaker icon with X
    # Speaker cone
    painter.drawPolygon([
        QPoint(int(cx - size * 0.4), int(cy - size * 0.3)),
        QPoint(int(cx - size * 0.1), int(cy - size * 0.3)),
        QPoint(int(cx + size * 0.3), int(cy - size * 0.5)),
        QPoint(int(cx + size * 0.3), int(cy + size * 0.5)),
        QPoint(int(cx - size * 0.1), int(cy + size * 0.3)),
        QPoint(int(cx - size * 0.4), int(cy + size * 0.3)),
    ])
    # X over speaker (muted indicator)
    painter.drawLine(int(cx + size * 0.1), int(cy - size * 0.2), int(cx + size * 0.4), int(cy + size * 0.2))
    painter.drawLine(int(cx + size * 0.4), int(cy - size * 0.2), int(cx + size * 0.1), int(cy + size * 0.2))


def _draw_mute_mic(painter, cx, cy, size, color):
    # Microphone icon with slash
    # Mic body
    painter.setBrush(color)
    painter.drawRoundedRect(int(cx - size * 0.15), int(cy - size * 0.4), int(size * 0.3), int(size * 0.5), 3, 3)
    # Mic stand
    painter.drawLine(int(cx), int(cy + size * 0.1), int(cx), int(cy + size * 0.4))
    painter.drawLine(int(cx - size * 0.25), int(cy + size * 0.4), int(cx + size * 0.25), int(cy + size * 0.4))
    # Arc at bottom
    painter.drawArc(int(cx - size * 0.3), int(cy - size * 0.1), int(size * 0.6), int(size * 0.4), 0, 180 * 16)
    # Slash through mic
    painter.drawLine(int(cx - size * 0.4), int(cy - size * 0.4), int(cx + size * 0.4), int(cy + size * 0.4))


def _draw_brightness(painter, cx, cy, size, color):
    # Sun icon with rays
    # Center circle
    painter.setBrush(color)
    painter.drawEllipse(QPoint(int(cx), int(cy)), int(size * 0.25), int(size * 0.25))
    # Rays
    painter.setBrush(Qt.BrushStyle.NoBrush)
    ray_len = size * 0.45
    ray_inner = size * 0.35
    for angle_deg in range(0, 360, 45):
        rad = math.radians(angle_deg)
        x1 = cx + ray_inner * math.cos(rad)
        y1 = cy + ray_inner * math.sin(rad)
        x2 = cx + ray_len * math.cos(rad)
        y2 = cy + ray_len * math.sin(rad)
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))


def _draw_unknown(painter, cx, cy, size, color):
    # Circle with ? for unknown items
    painter.drawEllipse(QPoint(int(cx), int(cy)), int(size * 0.4), int(size * 0.4))
