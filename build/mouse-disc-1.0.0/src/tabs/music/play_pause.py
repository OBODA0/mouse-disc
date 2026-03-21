"""Play/Pause toggle tab"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw play/pause icon (combined play triangle and pause bars)"""
    pen = QPen(color, max(1.5, size * 0.12))
    painter.setPen(pen)
    painter.setBrush(color)

    # Draw play triangle (pointing right)
    s = size * 0.35
    p1 = QPoint(int(cx - s * 0.5), int(cy - s * 0.6))
    p2 = QPoint(int(cx - s * 0.5), int(cy + s * 0.6))
    p3 = QPoint(int(cx + s * 0.7), int(cy))
    painter.drawPolygon([p1, p2, p3])

    # Draw pause bars (overlapping slightly)
    bar_w = size * 0.12
    bar_h = size * 0.5
    gap = size * 0.08
    offset_x = size * 0.15

    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(pen)
    # Left bar
    painter.drawLine(
        int(cx + offset_x), int(cy - bar_h * 0.5),
        int(cx + offset_x), int(cy + bar_h * 0.5)
    )
    # Right bar
    painter.drawLine(
        int(cx + offset_x + gap + bar_w), int(cy - bar_h * 0.5),
        int(cx + offset_x + gap + bar_w), int(cy + bar_h * 0.5)
    )


def _action():
    """Toggle play/pause"""
    try:
        subprocess.run(["playerctl", "play-pause"], check=False)
    except Exception as e:
        print(f"Error toggling play/pause: {e}")
    return False  # Keep menu open


tab = Tab(
    id="play_pause",
    label="",
    action="playerctl play-pause",
    action_type="command",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
