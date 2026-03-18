"""Action handlers for Mouse Disc"""
import subprocess
from typing import Callable, Dict
from config import DiscItem


class ActionExecutor:
    """Executes actions for menu items"""

    def __init__(self, toggle_callback: Callable[[str, bool], None]):
        """
        Initialize with a callback for toggle state updates
        toggle_callback(item_id, new_state) -> None
        """
        self.toggle_callback = toggle_callback
        self.handlers: Dict[str, Callable[[DiscItem], None]] = {
            "app": self._handle_app,
            "command": self._handle_command,
            "hyprland": self._handle_hyprland,
            "media": self._handle_media,
            "toggle": self._handle_toggle,
        }

    def execute(self, item: DiscItem) -> bool:
        """
        Execute an item's action
        Returns True if menu should close, False if it should stay open
        """
        handler = self.handlers.get(item.action_type)
        if handler:
            return handler(item)
        return True  # Close by default

    def _handle_app(self, item: DiscItem) -> bool:
        """Launch an application"""
        try:
            subprocess.Popen([item.action])
        except Exception as e:
            print(f"Error launching {item.action}: {e}")
        return True  # Close menu

    def _handle_command(self, item: DiscItem) -> bool:
        """Execute a shell command"""
        try:
            subprocess.Popen(item.action, shell=True)
        except Exception as e:
            print(f"Error executing command: {e}")
        return True  # Close menu

    def _handle_hyprland(self, item: DiscItem) -> bool:
        """Execute Hyprland command"""
        try:
            subprocess.run(["hyprctl", item.action])
        except Exception as e:
            print(f"Error running hyprctl: {e}")
        return True  # Close menu

    def _handle_media(self, item: DiscItem) -> bool:
        """Handle media control"""
        try:
            if item.action == "play-pause":
                subprocess.run(["playerctl", "play-pause"])
            elif item.action == "next":
                subprocess.run(["playerctl", "next"])
            elif item.action == "previous":
                subprocess.run(["playerctl", "previous"])
            elif item.action.startswith("volume"):
                change = item.action.split()[1] if " " in item.action else "5%"
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", change])
        except Exception as e:
            print(f"Error controlling media: {e}")
        return True  # Close menu

    def _handle_toggle(self, item: DiscItem) -> bool:
        """Toggle a setting and keep menu open"""
        new_state = not item.toggle_state
        item.toggle_state = new_state

        # Notify about toggle change
        self.toggle_callback(item.id, new_state)

        # Execute the actual toggle action
        try:
            if item.id == "wifi":
                subprocess.run(["nmcli", "radio", "wifi", "on" if new_state else "off"])
            elif item.id == "bluetooth":
                subprocess.run(["bluetoothctl", "power", "on" if new_state else "off"])
            else:
                # Generic toggle - just notify, actual implementation can be added
                print(f"Toggle {item.id}: {new_state}")
        except Exception as e:
            print(f"Error toggling {item.id}: {e}")

        return False  # Keep menu open for toggles
