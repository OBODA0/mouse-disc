"""Controls menu tab - contains system controls + brightness bar"""
import subprocess
import math
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt

from core.base_tab import MenuTab


def _draw_icon(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Draw sliders icon"""
    pen = QPen(color, max(1.5, size * 0.15))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Two vertical sliders with knobs
    for sx in [cx - size * 0.25, cx + size * 0.25]:
        painter.drawLine(int(sx), int(cy - size * 0.4), int(sx), int(cy + size * 0.4))
        # Knob at different positions
        knob_y = cy + (0.2 if sx < cx else -0.2) * size
        painter.drawRect(int(sx - size * 0.1), int(knob_y - size * 0.08), int(size * 0.2), int(size * 0.16))


def draw_brightness_bar(
    painter: QPainter,
    cx: float,
    cy: float,
    brightness_level: float,
    bar_radius: float,
    bar_thickness: float,
    colors: dict,
    first_angle: float = 150,
    last_angle: float = 210,
    anim_progress: float = 1.0
):
    """Draw the curved brightness bar for controls submenu with animation

    Args:
        painter: QPainter instance
        cx, cy: Center coordinates
        brightness_level: Current brightness (0.0 to 1.0)
        bar_radius: Radius of the bar from center
        bar_thickness: Thickness of the bar
        colors: Dict with 'controls_bar_empty' and 'controls_bar_fill' colors
        first_angle: Angle of first item (default 150 = bottom-left for controls)
        last_angle: Angle of last item (default 210 = top-left for controls)
        anim_progress: Animation progress 0.0 to 1.0 (bar grows from center)
    """
    # Qt system: 0=right, positive=counter-clockwise
    qt_start_angle = -last_angle
    qt_end_angle = -first_angle
    qt_span = qt_end_angle - qt_start_angle

    empty_color = QColor(colors.get("controls_bar_empty", "#3a3a3a"))
    fill_color = QColor(colors.get("controls_bar_fill", "#ffffff"))

    rect_size = bar_radius * 2

    # Calculate total span and center angle
    total_span = abs(qt_span)
    center_angle = qt_start_angle + qt_span / 2

    # Animation: bar grows from center outward
    anim = max(0.0, min(1.0, anim_progress))
    current_half_span = (total_span / 2) * anim

    # Calculate current angles based on animation progress
    curr_start_angle = center_angle - current_half_span
    curr_end_angle = center_angle + current_half_span
    curr_span = curr_end_angle - curr_start_angle

    # Calculate brightness within the visible portion
    # Map brightness to the currently visible arc
    if anim < 1.0:
        # During animation, show full brightness color (growing from center)
        pen = QPen(fill_color, bar_thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(
            int(cx - bar_radius), int(cy - bar_radius),
            int(rect_size), int(rect_size),
            int(curr_start_angle * 16), int(curr_span * 16)
        )
    else:
        # Full animation complete - show actual brightness level
        brightness_span = qt_span * brightness_level
        empty_span = qt_span - brightness_span

        # Draw empty portion (dark gray, from bottom/qt_start_angle upward)
        if empty_span > 0:
            pen = QPen(empty_color, bar_thickness)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(
                int(cx - bar_radius), int(cy - bar_radius),
                int(rect_size), int(rect_size),
                int(qt_start_angle * 16), int(empty_span * 16)
            )

        # Draw filled portion (white, from end of empty to top)
        if brightness_span > 0:
            pen = QPen(fill_color, bar_thickness)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(
                int(cx - bar_radius), int(cy - bar_radius),
                int(rect_size), int(rect_size),
                int((qt_start_angle + empty_span) * 16), int(brightness_span * 16)
            )


def check_brightness_bar_click(
    px: float,
    py: float,
    cx: float,
    cy: float,
    bar_radius: float,
    bar_thickness: float,
    first_angle: float = 150,
    last_angle: float = 210
) -> float:
    """Check if click is on brightness bar and return brightness level

    Args:
        px, py: Click position
        cx, cy: Center position
        bar_radius: Radius of the bar from center
        bar_thickness: Thickness of the bar
        first_angle: Angle of first item
        last_angle: Angle of last item

    Returns:
        Brightness level (0.0 to 1.0) or -1 if not on bar
    """
    dx = px - cx
    dy = py - cy
    dist_from_center = math.hypot(dx, dy)

    # Check if within bar thickness
    if abs(dist_from_center - bar_radius) > bar_thickness * 0.6:
        return -1

    # Mouse angle (in degrees, 0=right, clockwise)
    mouse_angle = math.degrees(math.atan2(dy, dx))
    if mouse_angle < 0:
        mouse_angle += 360

    # Normalize
    def normalize(a):
        while a < 0:
            a += 360
        while a >= 360:
            a -= 360
        return a

    norm_first = normalize(first_angle)
    norm_last = normalize(last_angle)
    norm_mouse = normalize(mouse_angle)

    # Check if within arc range
    angle_padding = 10
    if norm_first <= norm_last:
        in_range = norm_first - angle_padding <= norm_mouse <= norm_last + angle_padding
    else:
        in_range = (norm_mouse >= norm_first - angle_padding or
                   norm_mouse <= norm_last + angle_padding)

    if not in_range:
        return -1

    # Calculate brightness
    if norm_first <= norm_last:
        brightness = (norm_mouse - norm_first) / (norm_last - norm_first)
    else:
        if norm_mouse >= norm_first:
            brightness = (norm_mouse - norm_first) / (norm_last + 360 - norm_first)
        elif norm_mouse <= norm_last:
            brightness = (norm_mouse + 360 - norm_first) / (norm_last + 360 - norm_first)
        else:
            brightness = 0.5

    return max(0.0, min(1.0, brightness))


def apply_brightness(brightness_level: float):
    """Apply brightness to the system"""
    try:
        brightness_percent = int(brightness_level * 100)
        subprocess.run(["brightnessctl", "set", f"{brightness_percent}%"], check=False)
    except Exception as e:
        print(f"Error setting brightness: {e}")


def get_brightness_state() -> float:
    """Get current brightness level from system"""
    try:
        result = subprocess.run(
            ["brightnessctl", "get"],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            current = int(result.stdout.strip())
            max_result = subprocess.run(
                ["brightnessctl", "max"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if max_result.returncode == 0:
                max_val = int(max_result.stdout.strip())
                return current / max_val
    except Exception:
        pass
    return 1.0


tab = MenuTab(
    id="controls",
    label="Controls",
    color="#e8e8e8",
    children=["wifi", "bluetooth", "mute_speakers", "mute_mic"],
    icon_drawer=_draw_icon,
)
