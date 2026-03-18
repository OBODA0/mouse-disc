"""Perplexity AI launcher"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw Perplexity 'P' icon"""
    pen = QPen(color, max(2.0, size * 0.18))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # P shape
    p_width = size * 0.5
    p_height = size * 0.7
    loop_height = size * 0.4

    # Vertical line
    painter.drawLine(
        int(cx - p_width * 0.3), int(cy - p_height * 0.5),
        int(cx - p_width * 0.3), int(cy + p_height * 0.5)
    )

    # P loop (top part)
    painter.drawArc(
        int(cx - p_width * 0.3), int(cy - p_height * 0.5),
        int(p_width * 0.9), int(loop_height),
        0, 180 * 16  # Arc from 0 to 180 degrees
    )

    # Horizontal connector
    painter.drawLine(
        int(cx - p_width * 0.3), int(cy - p_height * 0.5 + loop_height * 0.5),
        int(cx + p_width * 0.3), int(cy - p_height * 0.5 + loop_height * 0.5)
    )


def _action():
    """Launch Perplexity in browser"""
    try:
        subprocess.Popen(["xdg-open", "https://perplexity.ai"])
    except Exception as e:
        print(f"Error launching Perplexity: {e}")
    return True


tab = Tab(
    id="perplexity",
    label="",
    action="https://perplexity.ai",
    action_type="app",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
