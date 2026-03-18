"""Browser tab - launches Firefox"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw globe icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Globe circle
    painter.drawEllipse(QPoint(int(cx), int(cy)), int(size * 0.5), int(size * 0.5))
    # Horizontal line
    painter.drawLine(int(cx), int(cy - size * 0.5), int(cx), int(cy + size * 0.5))
    # Vertical line
    painter.drawLine(int(cx - size * 0.5), int(cy), int(cx + size * 0.5), int(cy))
    # Arcs
    painter.drawArc(int(cx - size * 0.5), int(cy - size * 0.25), int(size), int(size * 0.5), 0, 180 * 16)
    painter.drawArc(int(cx - size * 0.5), int(cy - size * 0.25), int(size), int(size * 0.5), 0, -180 * 16)


def _action():
    """Launch firefox"""
    try:
        subprocess.Popen(["firefox"])
    except Exception as e:
        print(f"Error launching firefox: {e}")
    return True


tab = Tab(
    id="browser",
    label="",
    action="firefox",
    action_type="app",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
