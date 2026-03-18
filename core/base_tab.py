"""Base classes for tabs in Mouse Disc"""
from typing import Callable, Optional, List, TYPE_CHECKING
from PyQt6.QtGui import QPainter, QColor

if TYPE_CHECKING:
    from config import DiscItem


class Tab:
    """Base class for individual tabs"""

    def __init__(
        self,
        id: str,
        label: str = "",
        action: str = "",
        action_type: str = "app",  # app, command, toggle, hyprland, media
        color: str = "#e8e8e8",
        icon_drawer: Optional[Callable[[QPainter, float, float, float, QColor], None]] = None,
        action_handler: Optional[Callable[[], bool]] = None,
        sync_state: Optional[Callable[[], bool]] = None,
        toggle_state: bool = False,
    ):
        self.id = id
        self.label = label
        self.action = action
        self.action_type = action_type
        self.color = color
        self.icon_drawer = icon_drawer
        self.action_handler = action_handler
        self.sync_state = sync_state
        self.toggle_state = toggle_state

    def draw_icon(self, painter: QPainter, cx: float, cy: float, size: float, color: QColor):
        """Draw the tab icon. Uses custom drawer if provided, else default."""
        if self.icon_drawer:
            self.icon_drawer(painter, cx, cy, size, color)
            return True
        return False

    def execute(self) -> bool:
        """Execute the tab action. Returns True if menu should close."""
        if self.action_handler:
            return self.action_handler()
        return True  # Default: close menu

    def sync_toggle_state(self) -> bool:
        """Sync toggle state with system. Returns current state."""
        if self.sync_state:
            self.toggle_state = self.sync_state()
        return self.toggle_state

    def to_disc_item(self) -> 'DiscItem':
        """Convert to DiscItem for config"""
        from config import DiscItem
        return DiscItem(
            id=self.id,
            label=self.label,
            icon=self.id,
            action=self.action,
            action_type=self.action_type,
            color=self.color,
            toggle_state=self.toggle_state,
        )


class MenuTab(Tab):
    """Tab that contains a submenu"""

    def __init__(
        self,
        id: str,
        label: str = "",
        color: str = "#e8e8e8",
        children: Optional[List[str]] = None,
        icon_drawer: Optional[Callable[[QPainter, float, float, float, QColor], None]] = None,
    ):
        super().__init__(
            id=id,
            label=label,
            action_type="menu",
            color=color,
            icon_drawer=icon_drawer,
        )
        self.children = children or []

    def to_disc_item(self) -> 'DiscItem':
        """Convert to DiscItem - children resolved at runtime by registry"""
        from config import DiscItem
        return DiscItem(
            id=self.id,
            label=self.label,
            icon=self.id,
            action=self.action,
            action_type="menu",
            color=self.color,
            children=[],  # Filled by registry
        )
