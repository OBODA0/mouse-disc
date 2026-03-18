"""Mute Speakers toggle tab"""
import subprocess
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

from core.base_tab import Tab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw speaker with X icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Speaker cone
    painter.drawPolygon([
        QPoint(int(cx - size * 0.4), int(cy - size * 0.3)),
        QPoint(int(cx - size * 0.1), int(cy - size * 0.3)),
        QPoint(int(cx + size * 0.3), int(cy - size * 0.5)),
        QPoint(int(cx + size * 0.3), int(cy + size * 0.5)),
        QPoint(int(cx - size * 0.1), int(cy + size * 0.3)),
        QPoint(int(cx - size * 0.4), int(cy + size * 0.3)),
    ])

    # X over speaker (muted indicator)
    painter.drawLine(int(cx + size * 0.1), int(cy - size * 0.2), int(cx + size * 0.4), int(cy + size * 0.2))
    painter.drawLine(int(cx + size * 0.4), int(cy - size * 0.2), int(cx + size * 0.1), int(cy + size * 0.2))


def _get_default_sink() -> str:
    """Get the default PulseAudio sink name"""
    try:
        result = subprocess.run(
            ["pactl", "info"],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'default sink:' in line.lower():
                    return line.split(':')[1].strip()
    except Exception:
        pass
    return ""


def _sync_state() -> bool:
    """Get current speaker mute state from system

    Returns True if unmuted (showing red), False if muted (showing white)
    """
    try:
        sink_name = _get_default_sink()
        if not sink_name:
            return False

        result = subprocess.run(
            ["pactl", "list", "sinks"],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            in_default_sink = False
            for line in result.stdout.split('\n'):
                if f'Name: {sink_name}' in line:
                    in_default_sink = True
                elif in_default_sink and line.strip().startswith('Name:'):
                    in_default_sink = False
                if in_default_sink and 'Mute:' in line:
                    # "Mute: no" = unmuted = red = True
                    return 'no' in line.lower()
    except Exception:
        pass
    return False


def _toggle():
    """Execute the toggle action"""
    try:
        current_state = _sync_state()
        new_state = not current_state
        # new_state=True means unmuted (red), new_state=False means muted (white)
        subprocess.run(
            ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0" if new_state else "1"],
            check=False
        )
    except Exception as e:
        print(f"Error toggling speakers: {e}")


tab = Tab(
    id="mute_speakers",
    label="",
    action="mute_speakers",
    action_type="toggle",
    color="#e8e8e8",
    icon_drawer=_draw_icon,
    action_handler=_toggle,
    sync_state=_sync_state,
)
