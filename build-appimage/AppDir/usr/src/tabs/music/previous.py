"""Previous track tab"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw previous track icon (vertical bar + left arrow)"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(color)

    s = size * 0.35

    # Draw vertical bar at the start
    painter.setBrush(Qt.BrushStyle.NoBrush)
    bar_x = int(cx - s * 0.6)
    painter.drawLine(bar_x, int(cy - s * 0.6), bar_x, int(cy + s * 0.6))

    # Draw left-pointing triangle
    painter.setBrush(color)
    p1 = QPoint(int(cx - s * 0.3), int(cy))
    p2 = QPoint(int(cx + s * 0.5), int(cy - s * 0.6))
    p3 = QPoint(int(cx + s * 0.5), int(cy + s * 0.6))
    painter.drawPolygon([p1, p2, p3])


def _action():
    """Previous track"""
    try:
        subprocess.run(["playerctl", "previous"], check=False)
    except Exception as e:
        print(f"Error going to previous track: {e}")
    return False  # Keep menu open


tab = Tab(
    id="previous",
    label="Prev",
    action="playerctl previous",
    action_type="command",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
