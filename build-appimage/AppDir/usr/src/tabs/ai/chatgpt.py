"""ChatGPT launcher"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw ChatGPT hexagon icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Hexagon (ChatGPT logo style)
    hex_radius = size * 0.4
    hex_points = []
    for i in range(6):
        angle = -90 + i * 60  # Start from top
        x = cx + hex_radius * 0.9 * (1 if i % 3 == 0 else 0.5)
        if i == 0:
            x, y = cx, cy - hex_radius
        elif i == 1:
            x, y = cx + hex_radius * 0.85, cy - hex_radius * 0.5
        elif i == 2:
            x, y = cx + hex_radius * 0.85, cy + hex_radius * 0.5
        elif i == 3:
            x, y = cx, cy + hex_radius
        elif i == 4:
            x, y = cx - hex_radius * 0.85, cy + hex_radius * 0.5
        else:
            x, y = cx - hex_radius * 0.85, cy - hex_radius * 0.5
        hex_points.append(QPoint(int(x), int(y)))
    painter.drawPolygon(hex_points)

    # Inner lines forming abstract GPT shape
    inner_size = size * 0.2
    # Vertical segment
    painter.drawLine(
        int(cx - inner_size * 0.3), int(cy - inner_size),
        int(cx - inner_size * 0.3), int(cy + inner_size * 0.3)
    )
    # Diagonal segment
    painter.drawLine(
        int(cx - inner_size * 0.3), int(cy + inner_size * 0.3),
        int(cx + inner_size * 0.5), int(cy - inner_size)
    )


def _action():
    """Launch ChatGPT in browser"""
    try:
        subprocess.Popen(["xdg-open", "https://chat.openai.com"])
    except Exception as e:
        print(f"Error launching ChatGPT: {e}")
    return True


tab = Tab(
    id="chatgpt",
    label="GPT",
    action="https://chat.openai.com",
    action_type="app",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
