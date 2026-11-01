"""
MythoriaSolver UI Theme & Visual Styling Configuration
Colors, Typography (JetBrains Mono) and Antialiased Icon Loader.
"""
from pathlib import Path
from typing import Dict, Optional
from PIL import Image
import customtkinter as ctk

from config import config

# Typography
FONT_NAME = "JetBrains Mono"


def get_font(size: int = 12, weight: str = "normal", slant: str = "roman") -> ctk.CTkFont:
    """Helper to return consistent JetBrains Mono font."""
    return ctk.CTkFont(family=FONT_NAME, size=size, weight=weight, slant=slant)


# Obsidian Dark Color Palette
C_BG = "#0f1117"
C_SIDEBAR = "#161922"
C_CARD = "#1c202c"
C_CARD_HOVER = "#242938"
C_BORDER = "#2a3042"
C_ACCENT = "#38bdf8"
C_ACCENT_HOVER = "#0284c7"
C_SUCCESS = "#22c55e"
C_DANGER = "#ef4444"
C_WARNING = "#f59e0b"
C_TEXT = "#f8fafc"
C_TEXT_MUTED = "#94a3b8"


def load_icons() -> Dict[str, ctk.CTkImage]:
    """Loads 64x64 antialiased icons from assets/icons/ as CTkImage and sets up aliases."""
    icons_dir = config.ASSETS_DIR / "icons"
    icons: Dict[str, ctk.CTkImage] = {}

    icon_names = [
        "dashboard", "settings", "solvers", "stealth", "tabchi", "stats",
        "dashboard_active", "settings_active", "solvers_active",
        "stealth_active", "tabchi_active", "stats_active",
        "play", "stop", "save", "refresh", "folder", "plus", "trash", "bolt", "check"
    ]

    for name in icon_names:
        p = icons_dir / f"{name}.png"
        if p.exists():
            try:
                pil_img = Image.open(p)
                icons[name] = ctk.CTkImage(
                    light_image=pil_img,
                    dark_image=pil_img,
                    size=(20, 20)
                )
            except Exception:
                pass

    # Map tab_id to icon_name aliases
    nav_icon_map = {
        "dashboard": "dashboard",
        "general": "settings",
        "solvers": "solvers",
        "stealth": "stealth",
        "tabchi": "tabchi",
        "sandbox": "stats",
    }
    for tab_id, icon_name in nav_icon_map.items():
        if icon_name in icons and tab_id not in icons:
            icons[tab_id] = icons[icon_name]
        if f"{icon_name}_active" in icons and f"{tab_id}_active" not in icons:
            icons[f"{tab_id}_active"] = icons[f"{icon_name}_active"]

    # Larger App Logo for Sidebar
    logo_p = config.ASSETS_DIR / "app_icon.png"
    if logo_p.exists():
        try:
            pil_logo = Image.open(logo_p)
            icons["app_logo"] = ctk.CTkImage(
                light_image=pil_logo,
                dark_image=pil_logo,
                size=(36, 36)
            )
        except Exception:
            pass

    return icons
