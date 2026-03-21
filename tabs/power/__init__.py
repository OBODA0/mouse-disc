"""Power options menu tab - contains power control children"""
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import MenuTab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw power icon (circle with vertical line)"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Circle
    painter.drawEllipse(
        QPoint(int(cx), int(cy + size * 0.1)),
        int(size * 0.4), int(size * 0.4)
    )

    # Vertical line extending from top of circle
    painter.drawLine(
        int(cx), int(cy - size * 0.5),
        int(cx), int(cy)
    )


tab = MenuTab(
    id="power",
    label="Power",
    color="#e8e8e8",
    children=["shutdown", "reboot", "suspend", "lock"],
    icon_drawer=_draw_icon,
)
