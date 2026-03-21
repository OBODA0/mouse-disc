"""Zen Browser launcher"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw Z icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Z shape
    painter.drawLine(int(cx - size * 0.4), int(cy - size * 0.4), int(cx + size * 0.4), int(cy - size * 0.4))
    painter.drawLine(int(cx + size * 0.4), int(cy - size * 0.4), int(cx - size * 0.4), int(cy + size * 0.4))
    painter.drawLine(int(cx - size * 0.4), int(cy + size * 0.4), int(cx + size * 0.4), int(cy + size * 0.4))


def _action():
    """Launch Zen Browser"""
    try:
        subprocess.Popen(["zen-browser"])
    except Exception as e:
        print(f"Error launching zen-browser: {e}")
    return True


tab = Tab(
    id="zen",
    label="Zen",
    action="zen-browser",
    action_type="app",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
