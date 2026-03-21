"""Music menu tab - contains music playback controls"""
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import MenuTab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw music note icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(color)

    # Note head (circle)
    painter.drawEllipse(
        QPoint(int(cx - size * 0.2), int(cy + size * 0.3)),
        int(size * 0.25), int(size * 0.2)
    )

    # Stem
    painter.drawLine(
        int(cx + size * 0.05), int(cy + size * 0.3),
        int(cx + size * 0.05), int(cy - size * 0.4)
    )

    # Flag/curve
    painter.drawLine(
        int(cx + size * 0.05), int(cy - size * 0.4),
        int(cx + size * 0.4), int(cy - size * 0.1)
    )
    painter.drawLine(
        int(cx + size * 0.4), int(cy - size * 0.1),
        int(cx + size * 0.05), int(cy + size * 0.1)
    )


tab = MenuTab(
    id="music",
    label="Music",
    color="#e8e8e8",
    children=["previous", "backward10", "play_pause", "forward10", "next"],
    icon_drawer=_draw_icon,
)
