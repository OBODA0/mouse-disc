"""ZapZap (WhatsApp) launcher"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw lightning bolt/Z icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Lightning bolt shape
    painter.drawPolygon([
        QPoint(int(cx + size * 0.3), int(cy - size * 0.5)),
        QPoint(int(cx - size * 0.1), int(cy)),
        QPoint(int(cx + size * 0.2), int(cy)),
        QPoint(int(cx - size * 0.2), int(cy + size * 0.5)),
        QPoint(int(cx + size * 0.1), int(cy)),
        QPoint(int(cx - size * 0.4), int(cy)),
    ])


def _action():
    """Launch ZapZap"""
    try:
        subprocess.Popen(["zapzap"])
    except Exception as e:
        print(f"Error launching zapzap: {e}")
    return True


tab = Tab(
    id="zapzap",
    label="Zap",
    action="zapzap",
    action_type="app",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
