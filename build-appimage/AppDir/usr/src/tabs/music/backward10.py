"""Backward 10 seconds tab"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw backward 10 seconds icon (double left arrows)"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(color)

    # Draw two left-pointing triangles
    s = size * 0.3
    offset = size * 0.25

    # First triangle (leftmost)
    p1 = QPoint(int(cx - offset - s * 0.5), int(cy))
    p2 = QPoint(int(cx - offset + s * 0.3), int(cy - s * 0.5))
    p3 = QPoint(int(cx - offset + s * 0.3), int(cy + s * 0.5))
    painter.drawPolygon([p1, p2, p3])

    # Second triangle (right)
    p4 = QPoint(int(cx + offset - s * 0.5), int(cy))
    p5 = QPoint(int(cx + offset + s * 0.3), int(cy - s * 0.5))
    p6 = QPoint(int(cx + offset + s * 0.3), int(cy + s * 0.5))
    painter.drawPolygon([p4, p5, p6])


def _action():
    """Backward 10 seconds"""
    try:
        subprocess.run(["playerctl", "position", "-10"], check=False)
    except Exception as e:
        print(f"Error rewinding: {e}")
    return False  # Keep menu open


tab = Tab(
    id="backward10",
    label="-10s",
    action="playerctl position -10",
    action_type="command",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
