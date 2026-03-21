"""Antigravity app launcher"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw up arrow icon (antigravity)"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Up arrow
    painter.drawLine(int(cx), int(cy + size * 0.4), int(cx), int(cy - size * 0.4))
    painter.drawLine(int(cx - size * 0.4), int(cy), int(cx), int(cy - size * 0.4))
    painter.drawLine(int(cx + size * 0.4), int(cy), int(cx), int(cy - size * 0.4))


def _action():
    """Launch Antigravity"""
    try:
        subprocess.Popen(["antigravity"])
    except Exception as e:
        print(f"Error launching antigravity: {e}")
    return True


tab = Tab(
    id="antigravity",
    label="",
    action="antigravity",
    action_type="app",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
