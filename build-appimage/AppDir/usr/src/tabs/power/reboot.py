"""Reboot power option"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw reboot/restart icon (circular arrow)"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Circular arrow
    painter.drawArc(
        int(cx - size * 0.4), int(cy - size * 0.4),
        int(size * 0.8), int(size * 0.8),
        45 * 16, 270 * 16
    )

    # Arrow head
    painter.drawLine(
        int(cx + size * 0.3), int(cy - size * 0.3),
        int(cx + size * 0.4), int(cy - size * 0.4)
    )
    painter.drawLine(
        int(cx + size * 0.3), int(cy - size * 0.3),
        int(cx + size * 0.2), int(cy - size * 0.4)
    )


def _action():
    """Reboot system"""
    try:
        subprocess.Popen(["systemctl", "reboot"])
    except Exception as e:
        print(f"Error rebooting: {e}")
    return True


tab = Tab(
    id="reboot",
    label="Reboot",
    action="reboot",
    action_type="command",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
