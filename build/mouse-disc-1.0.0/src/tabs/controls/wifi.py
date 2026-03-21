"""WiFi toggle tab"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw WiFi icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Arcs for signal strength
    for i, r in enumerate([0.2, 0.4, 0.6]):
        painter.drawArc(
            int(cx - size * r), int(cy - size * r),
            int(size * r * 2), int(size * r * 2),
            45 * 16, 90 * 16
        )

    # Dot at bottom
    painter.setBrush(color)
    painter.drawEllipse(
        QPoint(int(cx), int(cy + size * 0.65)),
        int(size * 0.12), int(size * 0.12)
    )


def _sync_state() -> bool:
    """Get current WiFi state from system"""
    try:
        result = subprocess.run(
            ["nmcli", "radio", "wifi"],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            return "enabled" in result.stdout.lower()
    except Exception:
        pass
    return False


def _toggle() -> bool:
    """Execute the toggle action. Returns False to keep menu open."""
    try:
        current_state = _sync_state()
        new_state = not current_state
        subprocess.run(
            ["nmcli", "radio", "wifi", "on" if new_state else "off"],
            check=False
        )
        # Update the tab's toggle_state so UI reflects the change immediately
        tab.toggle_state = new_state
    except Exception as e:
        print(f"Error toggling wifi: {e}")
    return False  # Keep menu open for toggles


tab = Tab(
    id="wifi",
    label="",
    action="wifi",
    action_type="toggle",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_toggle,
    sync_state=_sync_state,
)
