"""Suspend power option"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw suspend/sleep icon (moon)"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Crescent moon shape
    # Outer arc
    painter.drawArc(
        int(cx - size * 0.5), int(cy - size * 0.5),
        int(size), int(size),
        -60 * 16, 240 * 16
    )
    # Inner arc
    painter.drawArc(
        int(cx - size * 0.3), int(cy - size * 0.5),
        int(size * 0.6), int(size),
        -90 * 16, 180 * 16
    )


def _action():
    """Suspend system"""
    try:
        subprocess.Popen(["systemctl", "suspend"])
    except Exception as e:
        print(f"Error suspending: {e}")
    return True


tab = Tab(
    id="suspend",
    label="Sleep",
    action="suspend",
    action_type="command",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
