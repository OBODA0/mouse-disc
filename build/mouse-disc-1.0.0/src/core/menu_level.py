"""Menu level class for Mouse Disc"""
from typing import List, Optional

from config import DiscItem, MenuStyle


class MenuLevel:
    """Represents one level of menu (main or submenu)"""
    def __init__(self, items: List[DiscItem], parent_angle: float = 0,
                 level: int = 0, parent_item: Optional[DiscItem] = None):
        self.items = items
        self.parent_angle = parent_angle  # Angle of parent (for submenus)
        self.level = level  # 0 = main, 1 = first submenu, etc.
        self.parent_item = parent_item
        self.hovered_index = -1
        self.expanded_child = None  # Which child submenu is expanded

    def get_style(self, config) -> MenuStyle:
        """Get the style for this menu level"""
        if self.level == 0:
            return config.main_style
        else:
            return config.sub_style
