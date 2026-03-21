"""Google Gemini AI launcher"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw Gemini diamond/star icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Diamond shape (Gemini logo style)
    diamond_size = size * 0.35
    painter.drawPolygon([
        QPoint(int(cx), int(cy - diamond_size)),
        QPoint(int(cx + diamond_size * 0.9), int(cy)),
        QPoint(int(cx), int(cy + diamond_size)),
        QPoint(int(cx - diamond_size * 0.9), int(cy)),
    ])

    # Inner cross lines
    painter.drawLine(int(cx), int(cy - diamond_size * 0.6), int(cx), int(cy + diamond_size * 0.6))
    painter.drawLine(int(cx - diamond_size * 0.5), int(cy), int(cx + diamond_size * 0.5), int(cy))


def _action():
    """Launch Gemini in browser"""
    try:
        subprocess.Popen(["xdg-open", "https://gemini.google.com"])
    except Exception as e:
        print(f"Error launching Gemini: {e}")
    return True


tab = Tab(
    id="gemini",
    label="Gem",
    action="https://gemini.google.com",
    action_type="app",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
