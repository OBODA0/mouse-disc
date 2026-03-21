"""Obsidian app launcher"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw Obsidian crystal/gem icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Crystal polygon
    painter.drawPolygon([
        QPoint(int(cx), int(cy - size * 0.6)),
        QPoint(int(cx + size * 0.5), int(cy - size * 0.2)),
        QPoint(int(cx + size * 0.3), int(cy + size * 0.5)),
        QPoint(int(cx - size * 0.3), int(cy + size * 0.5)),
        QPoint(int(cx - size * 0.5), int(cy - size * 0.2)),
    ])


def _action():
    """Launch Obsidian"""
    try:
        subprocess.Popen(["obsidian"])
    except Exception as e:
        print(f"Error launching obsidian: {e}")
    return True


tab = Tab(
    id="obsidian",
    label="",
    action="obsidian",
    action_type="app",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
