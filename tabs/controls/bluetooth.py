"""Bluetooth toggle tab"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw Bluetooth icon (rune symbol)"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Vertical line
    painter.drawLine(int(cx), int(cy - size * 0.5), int(cx), int(cy + size * 0.5))

    # Left triangle
    painter.drawLine(int(cx - size * 0.3), int(cy - size * 0.25), int(cx), int(cy))
    painter.drawLine(int(cx - size * 0.3), int(cy + size * 0.25), int(cx), int(cy))

    # Right triangle
    painter.drawLine(int(cx), int(cy), int(cx + size * 0.3), int(cy - size * 0.25))
    painter.drawLine(int(cx), int(cy), int(cx + size * 0.3), int(cy + size * 0.25))


def _sync_state() -> bool:
    """Get current Bluetooth state from system"""
    try:
        result = subprocess.run(
            ["bluetoothctl", "show"],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            return "powered: yes" in result.stdout.lower()
    except Exception:
        pass
    return False


def _toggle():
    """Execute the toggle action"""
    try:
        current_state = _sync_state()
        new_state = not current_state
        subprocess.run(
            ["bluetoothctl", "power", "on" if new_state else "off"],
            check=False
        )
    except Exception as e:
        print(f"Error toggling bluetooth: {e}")


tab = Tab(
    id="bluetooth",
    label="",
    action="bluetooth",
    action_type="toggle",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_toggle,
    sync_state=_sync_state,
)
