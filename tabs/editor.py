"""Editor tab - launches VS Code"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw code brackets icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Left bracket <
    painter.drawLine(int(cx - size * 0.4), int(cy - size * 0.3), int(cx - size * 0.6), int(cy))
    painter.drawLine(int(cx - size * 0.6), int(cy), int(cx - size * 0.4), int(cy + size * 0.3))

    # Right bracket />
    painter.drawLine(int(cx + size * 0.4), int(cy - size * 0.3), int(cx + size * 0.6), int(cy))
    painter.drawLine(int(cx + size * 0.6), int(cy), int(cx + size * 0.4), int(cy + size * 0.3))

    # Slash /
    painter.drawLine(int(cx - size * 0.1), int(cy - size * 0.4), int(cx + size * 0.1), int(cy + size * 0.4))


def _action():
    """Launch VS Code"""
    try:
        subprocess.Popen(["code"])
    except Exception as e:
        print(f"Error launching code: {e}")
    return True


tab = Tab(
    id="editor",
    label="",
    action="code",
    action_type="app",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
