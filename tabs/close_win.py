"""Close window tab - closes active Hyprland window"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw X icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # X shape
    painter.drawLine(
        int(cx - size * 0.5), int(cy - size * 0.5),
        int(cx + size * 0.5), int(cy + size * 0.5)
    )
    painter.drawLine(
        int(cx + size * 0.5), int(cy - size * 0.5),
        int(cx - size * 0.5), int(cy + size * 0.5)
    )


def _action():
    """Close active window via Hyprland"""
    try:
        subprocess.run(["hyprctl", "dispatch", "killactive"], check=False)
    except Exception as e:
        print(f"Error closing window: {e}")
    return True


tab = Tab(
    id="close_win",
    label="",
    action="killactive",
    action_type="hyprland",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
