"""Lock screen power option"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw lock icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    lock_w = size * 0.8
    lock_h = size * 0.6

    # Lock body
    painter.drawRoundedRect(
        int(cx - lock_w/2), int(cy - lock_h/2 + size * 0.2),
        int(lock_w), int(lock_h), 3, 3
    )

    # Lock shackle (arc)
    painter.drawArc(
        int(cx - lock_w/2), int(cy - size * 0.6),
        int(lock_w), int(size * 0.8),
        0, 180 * 16
    )

    # Keyhole
    painter.setBrush(color)
    painter.drawEllipse(
        QPoint(int(cx), int(cy + size * 0.1)),
        int(size * 0.1), int(size * 0.1)
    )
    painter.drawLine(
        int(cx), int(cy + size * 0.1),
        int(cx), int(cy + size * 0.3)
    )


def _action():
    """Lock screen"""
    try:
        subprocess.Popen(["hyprlock"])
    except Exception as e:
        print(f"Error locking: {e}")
    return True


tab = Tab(
    id="lock",
    label="Lock",
    action="hyprlock",
    action_type="command",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
