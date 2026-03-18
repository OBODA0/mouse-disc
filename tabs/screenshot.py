"""Screenshot tab - captures screen region"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw camera/screenshot icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    frame_size = size * 1.2
    # Frame rectangle
    painter.drawRect(
        int(cx - frame_size/2), int(cy - frame_size/2),
        int(frame_size), int(frame_size)
    )

    # Corner markers
    corner = size * 0.3
    for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        px = cx + dx * frame_size/2
        py = cy + dy * frame_size/2
        painter.drawLine(int(px), int(py - dy * corner), int(px), int(py))
        painter.drawLine(int(px - dx * corner), int(py), int(px), int(py))

    # Center dot
    painter.setBrush(color)
    painter.drawEllipse(QPoint(int(cx), int(cy)), int(size * 0.2), int(size * 0.2))


def _action():
    """Take screenshot with region selection"""
    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        subprocess.Popen(
            f"grim -g $(slurp) ~/Pictures/{timestamp}.png",
            shell=True
        )
    except Exception as e:
        print(f"Error taking screenshot: {e}")
    return True


tab = Tab(
    id="screenshot",
    label="",
    action="grim -g $(slurp) ~/Pictures/$(date +%Y%m%d_%H%M%S).png",
    action_type="command",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_action,
)
