"""Apps menu tab - contains application launcher children"""
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import MenuTab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw 2x2 grid of squares icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    sq = size * 0.35
    gap = size * 0.1
    for dx in [-1, 1]:
        for dy in [-1, 1]:
            sx = cx + dx * (sq/2 + gap/2)
            sy = cy + dy * (sq/2 + gap/2)
            painter.drawRect(int(sx - sq/2), int(sy - sq/2), int(sq), int(sq))


tab = MenuTab(
    id="apps",
    label="Apps",
    color="#e8e8e8",
    children=["obsidian", "antigravity", "zen", "zapzap"],
    icon_drawer=_draw_icon,
)
