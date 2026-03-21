"""Claude AI launcher"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw Claude 'C' / swirl icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Outer C shape (Claude style spiral)
    c_radius = size * 0.35

    # Draw spiral/C shape with arcs
    # Top arc
    painter.drawArc(
        int(cx - c_radius), int(cy - c_radius),
        int(c_radius * 2), int(c_radius * 2),
        45 * 16, 135 * 16
    )

    # Left vertical
    painter.drawLine(
        int(cx - c_radius * 0.7), int(cy - c_radius * 0.4),
        int(cx - c_radius * 0.7), int(cy + c_radius * 0.4)
    )

    # Bottom arc
    painter.drawArc(
        int(cx - c_radius), int(cy - c_radius * 0.2),
        int(c_radius * 2), int(c_radius * 1.4),
        225 * 16, 90 * 16
    )

    # Inner dot
    dot_size = size * 0.08
    painter.drawEllipse(
        int(cx + c_radius * 0.2), int(cy - dot_size / 2),
        int(dot_size), int(dot_size)
    )


def _action():
    """Launch Claude in browser"""
    try:
        subprocess.Popen(["xdg-open", "https://claude.ai"])
    except Exception as e:
        print(f"Error launching Claude: {e}")
    return True


tab = Tab(
    id="claude",
    label="Claud",
    action="https://claude.ai",
    action_type="app",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
