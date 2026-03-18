"""AI shortcuts menu tab - contains AI service launcher children"""
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import MenuTab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw AI brain/sparkles icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Central hexagon (brain shape)
    hex_radius = size * 0.35
    hex_points = []
    for i in range(6):
        if i == 0:
            x, y = cx, cy - hex_radius * 0.8
        elif i == 1:
            x, y = cx + hex_radius * 0.7, cy - hex_radius * 0.4
        elif i == 2:
            x, y = cx + hex_radius * 0.7, cy + hex_radius * 0.4
        elif i == 3:
            x, y = cx, cy + hex_radius * 0.8
        elif i == 4:
            x, y = cx - hex_radius * 0.7, cy + hex_radius * 0.4
        else:
            x, y = cx - hex_radius * 0.7, cy - hex_radius * 0.4
        hex_points.append(QPoint(int(x), int(y)))
    painter.drawPolygon(hex_points)

    # Circuit lines inside
    painter.drawLine(int(cx), int(cy - hex_radius * 0.4), int(cx), int(cy))
    painter.drawLine(int(cx), int(cy), int(cx + hex_radius * 0.4), int(cy + hex_radius * 0.2))
    painter.drawLine(int(cx), int(cy), int(cx - hex_radius * 0.4), int(cy + hex_radius * 0.2))

    # Sparkles around
    sparkle_size = size * 0.12
    sparkles = [
        (cx - size * 0.5, cy - size * 0.5),
        (cx + size * 0.55, cy - size * 0.35),
        (cx + size * 0.45, cy + size * 0.5),
    ]
    for sx, sy in sparkles:
        painter.drawLine(int(sx - sparkle_size), int(sy), int(sx + sparkle_size), int(sy))
        painter.drawLine(int(sx), int(sy - sparkle_size), int(sx), int(sy + sparkle_size))


tab = MenuTab(
    id="ai",
    label="",
    color="#e8e8e8",
    children=["perplexity", "gemini", "claude", "chatgpt"],
    icon_drawer=_draw_icon,
)
