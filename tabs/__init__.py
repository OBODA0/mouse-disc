"""Tabs package for Mouse Disc - Auto-discovery and registry"""
import os
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Callable
from PyQt6.QtGui import QPainter, QColor

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.base_tab import Tab, MenuTab
from config import DiscItem


class TabRegistry:
    """Registry for all tabs"""

    def __init__(self):
        self._tabs: Dict[str, Tab] = {}
        self._icon_drawers: Dict[str, Callable[[QPainter, float, float, float, QColor], None]] = {}
        self._discovered = False

    def register(self, tab: Tab):
        """Register a tab"""
        self._tabs[tab.id] = tab

    def get(self, tab_id: str) -> Optional[Tab]:
        """Get a tab by ID"""
        return self._tabs.get(tab_id)

    def get_icon_drawer(self, tab_id: str) -> Optional[Callable]:
        """Get icon drawer for a tab"""
        tab = self._tabs.get(tab_id)
        if tab and tab.icon_drawer:
            return tab.icon_drawer
        return self._icon_drawers.get(tab_id)

    def register_icon_drawer(self, item_id: str, drawer: Callable[[QPainter, float, float, float, QColor], None]):
        """Register an icon drawer for an item ID"""
        self._icon_drawers[item_id] = drawer

    def get_main_items(self) -> List[DiscItem]:
        """Get list of DiscItems for the main menu"""
        items = []
        for tab_id, tab in self._tabs.items():
            if not isinstance(tab, MenuTab):
                continue
            # Only include top-level menu tabs
            if tab_id in ["apps", "controls"]:
                disc_item = self._menu_tab_to_disc_item(tab)
                items.append(disc_item)
        return items

    def get_all_items(self) -> List[DiscItem]:
        """Get all items as DiscItems for backward compatibility

        Order (8 items, starting from top at -90 degrees):
        0: music (top)
        1: placeholder1 (top-right)
        2: placeholder2 (right)
        3: placeholder3 (bottom-right)
        4: power (bottom)
        5: apps (bottom-left)
        6: controls (left)
        7: ai (top-left)
        """
        items = []
        order = [
            "music",       # 0 - top
            "editor",      # 1 - top-right (placeholder for now)
            "screenshot",  # 2 - right (placeholder for now)
            "terminal",    # 3 - bottom-right (placeholder for now)
            "power",       # 4 - bottom
            "apps",        # 5 - bottom-left
            "controls",    # 6 - left
            "ai",          # 7 - top-left
        ]

        for tab_id in order:
            if tab_id not in self._tabs:
                continue
            tab = self._tabs[tab_id]
            if isinstance(tab, MenuTab):
                items.append(self._menu_tab_to_disc_item(tab))
            else:
                items.append(tab.to_disc_item())

        return items

    def _menu_tab_to_disc_item(self, menu_tab: MenuTab) -> DiscItem:
        """Convert MenuTab to DiscItem with resolved children"""
        children = []
        for child_id in menu_tab.children:
            child_tab = self._tabs.get(child_id)
            if child_tab:
                children.append(child_tab.to_disc_item())

        return DiscItem(
            id=menu_tab.id,
            label=menu_tab.label,
            icon=menu_tab.id,
            action=menu_tab.action,
            action_type="menu",
            color=menu_tab.color,
            children=children,
        )

    def discover(self):
        """Discover all tabs from the tabs directory"""
        if self._discovered:
            return

        tabs_dir = Path(__file__).parent

        # Import simple tabs (music is now a menu with children)
        simple_tabs = ["terminal", "editor", "screenshot"]
        for tab_name in simple_tabs:
            try:
                module = importlib.import_module(f"tabs.{tab_name}")
                if hasattr(module, "tab"):
                    self.register(module.tab)
            except Exception as e:
                print(f"Error loading tab {tab_name}: {e}")

        # Import apps menu and children
        try:
            apps_module = importlib.import_module("tabs.apps")
            if hasattr(apps_module, "tab"):
                self.register(apps_module.tab)
                # Import children
                for child_name in ["obsidian", "antigravity", "zen", "zapzap"]:
                    try:
                        child_module = importlib.import_module(f"tabs.apps.{child_name}")
                        if hasattr(child_module, "tab"):
                            self.register(child_module.tab)
                    except Exception as e:
                        print(f"Error loading apps child {child_name}: {e}")
        except Exception as e:
            print(f"Error loading apps module: {e}")

        # Import controls menu and children
        try:
            controls_module = importlib.import_module("tabs.controls")
            if hasattr(controls_module, "tab"):
                self.register(controls_module.tab)
                # Import children
                for child_name in ["wifi", "bluetooth", "mute_speakers", "mute_mic"]:
                    try:
                        child_module = importlib.import_module(f"tabs.controls.{child_name}")
                        if hasattr(child_module, "tab"):
                            self.register(child_module.tab)
                    except Exception as e:
                        print(f"Error loading controls child {child_name}: {e}")
        except Exception as e:
            print(f"Error loading controls module: {e}")

        # Import music menu and children
        try:
            music_module = importlib.import_module("tabs.music")
            if hasattr(music_module, "tab"):
                self.register(music_module.tab)
                # Import children
                for child_name in ["previous", "backward10", "play_pause", "forward10", "next"]:
                    try:
                        child_module = importlib.import_module(f"tabs.music.{child_name}")
                        if hasattr(child_module, "tab"):
                            self.register(child_module.tab)
                    except Exception as e:
                        print(f"Error loading music child {child_name}: {e}")
        except Exception as e:
            print(f"Error loading music module: {e}")

        # Import ai menu and children
        try:
            ai_module = importlib.import_module("tabs.ai")
            if hasattr(ai_module, "tab"):
                self.register(ai_module.tab)
                # Import children
                for child_name in ["perplexity", "gemini", "claude", "chatgpt"]:
                    try:
                        child_module = importlib.import_module(f"tabs.ai.{child_name}")
                        if hasattr(child_module, "tab"):
                            self.register(child_module.tab)
                    except Exception as e:
                        print(f"Error loading ai child {child_name}: {e}")
        except Exception as e:
            print(f"Error loading ai module: {e}")

        # Import power menu and children
        try:
            power_module = importlib.import_module("tabs.power")
            if hasattr(power_module, "tab"):
                self.register(power_module.tab)
                # Import children
                for child_name in ["shutdown", "reboot", "suspend", "lock"]:
                    try:
                        child_module = importlib.import_module(f"tabs.power.{child_name}")
                        if hasattr(child_module, "tab"):
                            self.register(child_module.tab)
                    except Exception as e:
                        print(f"Error loading power child {child_name}: {e}")
        except Exception as e:
            print(f"Error loading power module: {e}")

        self._discovered = True


# Global registry instance
_registry = TabRegistry()


def get_registry() -> TabRegistry:
    """Get the global tab registry"""
    if not _registry._discovered:
        _registry.discover()
    return _registry


# Backwards compatibility - direct access to items
def get_items() -> List[DiscItem]:
    """Get all menu items as DiscItems"""
    return get_registry().get_all_items()


def get_tab(tab_id: str) -> Optional[Tab]:
    """Get a tab by ID"""
    return get_registry().get(tab_id)
