"""Configuration management for Mouse Disc"""
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class DiscItem:
    """A menu item - can be app, command, toggle, or submenu"""
    id: str
    label: str = ""
    icon: str = ""
    action: str = ""
    action_type: str = "app"  # app, command, toggle, menu
    color: str = "#e8e8e8"
    toggle_state: bool = False
    children: List['DiscItem'] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        result = {
            "id": self.id,
            "label": self.label,
            "icon": self.icon,
            "action": self.action,
            "action_type": self.action_type,
            "color": self.color,
        }
        if self.toggle_state:
            result["toggle_state"] = True
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'DiscItem':
        """Create from dictionary"""
        children = data.get("children", [])
        return cls(
            id=data["id"],
            label=data.get("label", ""),
            icon=data.get("icon", ""),
            action=data.get("action", ""),
            action_type=data.get("action_type", "app"),
            color=data.get("color", "#e8e8e8"),
            toggle_state=data.get("toggle_state", False),
            children=[cls.from_dict(c) for c in children]
        )


@dataclass
class MenuStyle:
    """Styling for menu levels"""
    spread_radius: int = 112
    dot_radius: int = 35
    hover_growth: int = 5
    hit_radius: int = 50
    corridor_width: int = 80
    sub_spacing_factor: float = 0.6  # 60% of main spacing for sub-items


@dataclass
class Config:
    """Full application configuration"""
    items: List[DiscItem]
    main_style: MenuStyle
    sub_style: MenuStyle
    colors: Dict[str, str]
    settings: Dict[str, Any]

    @classmethod
    def default(cls) -> 'Config':
        """Create default configuration"""
        return cls(
            items=[
                DiscItem("browser", action="firefox"),
                DiscItem("terminal", action="kitty"),
                DiscItem("editor", action="code"),
                DiscItem("music", action="playerctl play-pause", action_type="command"),
                DiscItem("screenshot", action="grim -g $(slurp) ~/Pictures/$(date +%Y%m%d_%H%M%S).png", action_type="command"),
                DiscItem("lock", action="hyprlock", action_type="command"),
                DiscItem("apps", action_type="menu", children=[
                    DiscItem("obsidian", action="obsidian"),
                    DiscItem("antigravity", action="antigravity"),
                    DiscItem("zen", action="zen-browser"),
                    DiscItem("zapzap", action="zapzap"),
                ]),
                DiscItem("controls", action_type="menu", children=[
                    DiscItem("wifi", action="wifi", action_type="toggle"),
                    DiscItem("bluetooth", action="bluetooth", action_type="toggle"),
                ]),
            ],
            main_style=MenuStyle(
                spread_radius=112,
                dot_radius=35,
                hover_growth=5,
                hit_radius=50,
                corridor_width=80,
                sub_spacing_factor=0.6,
            ),
            sub_style=MenuStyle(
                spread_radius=224,  # Double
                dot_radius=35,  # Same size
                hover_growth=5,
                hit_radius=50,
                corridor_width=80,
                sub_spacing_factor=0.6,
            ),
            colors={
                "normal": "#e8e8e8",
                "hover": "#ffffff",
                "toggle_on": "#ff5050",
                "toggle_on_hover": "#ff6060",
                "icon": "#282828",
                "center_close": "#ffffff",
            },
            settings={
                "center_radius": 25,
                "close_hit_radius": 25,
            }
        )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "items": [item.to_dict() for item in self.items],
            "main_style": asdict(self.main_style),
            "sub_style": asdict(self.sub_style),
            "colors": self.colors,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        """Create from dictionary"""
        return cls(
            items=[DiscItem.from_dict(i) for i in data.get("items", [])],
            main_style=MenuStyle(**data.get("main_style", {})),
            sub_style=MenuStyle(**data.get("sub_style", {})),
            colors=data.get("colors", {}),
            settings=data.get("settings", {}),
        )


class ConfigManager:
    """Manages loading and saving configuration"""

    def __init__(self, config_path: str = "~/.config/mouse-disc/config.json"):
        self.config_path = Path(config_path).expanduser()
        self.config = self.load()

    def load(self) -> Config:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                return Config.from_dict(data)
            except Exception as e:
                print(f"Error loading config: {e}")
                return Config.default()
        else:
            config = Config.default()
            self.save(config)
            return config

    def save(self, config: Config):
        """Save configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
