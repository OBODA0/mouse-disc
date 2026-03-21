"""Terminal tab - launches Kitty"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw terminal prompt icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Terminal rectangle
    painter.drawRoundedRect(
        int(cx - size * 0.55), int(cy - size * 0.4),
        int(size * 1.1), int(size * 0.8), 4, 4
    )
    # Prompt text
    painter.drawText(int(cx - size * 0.35), int(cy + size * 0.15), ">_")


def _action():
    """Launch kitty terminal"""
    try:
        subprocess.Popen(["kitty"])
    except Exception as e:
        print(f"Error launching kitty: {e}")
    return True


tab = Tab(
    id="terminal",
    label="Terminal",
    action="kitty",
    action_type="app",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
