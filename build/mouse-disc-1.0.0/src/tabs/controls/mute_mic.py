"""Mute Microphone toggle tab"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw microphone with slash icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(color)

    # Mic body
    painter.drawRoundedRect(
        int(cx - size * 0.15), int(cy - size * 0.4),
        int(size * 0.3), int(size * 0.5), 3, 3
    )

    # Mic stand
    painter.drawLine(int(cx), int(cy + size * 0.1), int(cx), int(cy + size * 0.4))
    painter.drawLine(int(cx - size * 0.25), int(cy + size * 0.4), int(cx + size * 0.25), int(cy + size * 0.4))

    # Arc at bottom
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(
        int(cx - size * 0.3), int(cy - size * 0.1),
        int(size * 0.6), int(size * 0.4), 0, 180 * 16
    )

    # Slash through mic
    painter.drawLine(int(cx - size * 0.4), int(cy - size * 0.4), int(cx + size * 0.4), int(cy + size * 0.4))


def _get_default_source() -> str:
    """Get the default PulseAudio source name"""
    try:
        result = subprocess.run(
            ["pactl", "info"],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'default source:' in line.lower():
                    return line.split(':')[1].strip()
    except Exception:
        pass
    return ""


def _sync_state() -> bool:
    """Get current mic mute state from system

    Returns True if unmuted (showing red), False if muted (showing white)
    """
    try:
        source_name = _get_default_source()
        if not source_name:
            return False

        result = subprocess.run(
            ["pactl", "list", "sources"],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            in_default_source = False
            for line in result.stdout.split('\n'):
                if f'Name: {source_name}' in line:
                    in_default_source = True
                elif in_default_source and line.strip().startswith('Name:'):
                    in_default_source = False
                if in_default_source and 'Mute:' in line:
                    # "Mute: no" = unmuted = red = True
                    return 'no' in line.lower()
    except Exception:
        pass
    return False


def _toggle() -> bool:
    """Execute the toggle action. Returns False to keep menu open."""
    try:
        current_state = _sync_state()
        new_state = not current_state
        # new_state=True means unmuted (red), new_state=False means muted (white)
        subprocess.run(
            ["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "0" if new_state else "1"],
            check=False
        )
        # Update the tab's toggle_state so UI reflects the change immediately
        tab.toggle_state = new_state
    except Exception as e:
        print(f"Error toggling mic: {e}")
    return False  # Keep menu open for toggles


tab = Tab(
    id="mute_mic",
    label="",
    action="mute_mic",
    action_type="toggle",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_toggle,
    sync_state=_sync_state,
)
