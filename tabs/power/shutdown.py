"""Shutdown power option"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw power off icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Circle
    from PyQt6.QtCore import QPoint
    painter.drawEllipse(
        QPoint(int(cx), int(cy + size * 0.1)),
        int(size * 0.4), int(size * 0.4)
    )

    # Vertical line at top
    painter.drawLine(int(cx), int(cy - size * 0.5), int(cx), int(cy - size * 0.1))


def _action():
    """Shutdown system"""
    try:
        subprocess.Popen(["systemctl", "poweroff"])
    except Exception as e:
        print(f"Error shutting down: {e}")
    return True


tab = Tab(
    id="shutdown",
    label="Off",
    action="poweroff",
    action_type="command",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
