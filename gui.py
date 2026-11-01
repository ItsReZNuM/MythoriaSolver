"""
MythoriaSolver - Modern CustomTkinter GUI
Features:
  - Deep Obsidian Dark Theme
  - JetBrains Mono Typography
  - Antialiased Icon Set (No emojis) with full icon mapping
  - Butter-Smooth Instant Tab Switching (tkraise z-order, zero-flicker)
  - APPDATA Settings Storage (%APPDATA%/MythoriaSolver/settings.json)
  - 6 Specialized Tabs:
      1. Dashboard & Live Bot Monitor
      2. General & Minecraft Configuration
      3. Solvers & Game-Type Delays
      4. Stealth & Human Typo Anti-Cheat
      5. Tabchi / Auto-Advertiser Manager
      6. Interactive Solver Sandbox & Live Stats
  - Real-time Thread-safe Event Bridge
  - Minecraft Launcher Auto-Detector
"""
import sys
import os
import time
import queue
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
from PIL import Image

import customtkinter as ctk
from tkinter import filedialog, messagebox

from config import config
from settings import (
    Settings,
    settings as global_settings,
    GAME_TYPES,
    GAME_TYPE_LABELS,
    GameTypeDelay,
    StealthSettings,
    TabchiSettings,
    DEFAULT_TABCHI_MESSAGES,
    SETTINGS_FILE,
)
from minecraft.log_finder import detect_minecraft_logs, MinecraftInstance
from solver.router import SolverRouter
from database.models import DatabaseManager

# Appearance Configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT_NAME = "JetBrains Mono"


def get_font(size: int = 12, weight: str = "normal", slant: str = "roman") -> ctk.CTkFont:
    """Helper to return consistent JetBrains Mono font."""
    return ctk.CTkFont(family=FONT_NAME, size=size, weight=weight, slant=slant)


class MythoriaGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Hide window off-screen during widget hierarchy construction
        # to eliminate startup flickering, layout pop-in, and black canvas flashes
        self.withdraw()

        self.title("MythoriaSolver ⚡ High-Performance SMP Chat Game Bot")

        # Center the window on screen
        win_w, win_h = 1100, 780
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        pos_x = max(0, (sw - win_w) // 2)
        pos_y = max(0, (sh - win_h) // 2)
        self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.minsize(980, 680)

        # Set Window Icon if present
        icon_path = config.ASSETS_DIR / "app_icon.ico"
        if icon_path.exists() and sys.platform == "win32":
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        # Load Active Settings from %APPDATA%/MythoriaSolver/settings.json
        self.settings = Settings.load()

        # Database and Router (Instant instances)
        self.db = DatabaseManager.get_instance()
        self.router = SolverRouter(self.db)

        # Bot Thread & Queue Management
        self.bot_instance = None
        self.bot_thread: Optional[threading.Thread] = None
        self.event_queue: queue.Queue = queue.Queue()
        self.is_running = False

        # Live Session Counters
        self.stats_games = 0
        self.stats_wins = 0
        self.stats_ads = 0

        # Load Custom PNG Icons
        self._load_icons()

        # Color Palette
        self.C_BG = "#0f1117"
        self.C_SIDEBAR = "#161922"
        self.C_CARD = "#1c202c"
        self.C_CARD_HOVER = "#242938"
        self.C_BORDER = "#2a3042"
        self.C_ACCENT = "#38bdf8"
        self.C_ACCENT_HOVER = "#0284c7"
        self.C_SUCCESS = "#22c55e"
        self.C_DANGER = "#ef4444"
        self.C_WARNING = "#f59e0b"
        self.C_TEXT = "#f8fafc"
        self.C_TEXT_MUTED = "#94a3b8"

        self.configure(fg_color=self.C_BG)

        # Build Main UI Layout
        self._create_layout()

        # Load settings into all UI controls
        self._populate_all_settings()

        # Start Event Queue Poller
        self.after(50, self._process_event_queue)

        # Force off-screen layout completion and smoothly reveal window
        self.update_idletasks()
        self.after(20, self.deiconify)

    # ── Icon Loader ──────────────────────────────────────────────────────────
    def _load_icons(self):
        """Loads 64x64 icons from assets/icons/ as CTkImage and sets up aliases."""
        icons_dir = config.ASSETS_DIR / "icons"
        self.icons: Dict[str, ctk.CTkImage] = {}

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
                    self.icons[name] = ctk.CTkImage(
                        light_image=pil_img,
                        dark_image=pil_img,
                        size=(20, 20)
                    )
                except Exception:
                    pass

        # Map tab_id to icon_name aliases
        self.nav_icon_map = {
            "dashboard": "dashboard",
            "general": "settings",
            "solvers": "solvers",
            "stealth": "stealth",
            "tabchi": "tabchi",
            "sandbox": "stats",
        }
        for tab_id, icon_name in self.nav_icon_map.items():
            if icon_name in self.icons and tab_id not in self.icons:
                self.icons[tab_id] = self.icons[icon_name]
            if f"{icon_name}_active" in self.icons and f"{tab_id}_active" not in self.icons:
                self.icons[f"{tab_id}_active"] = self.icons[f"{icon_name}_active"]

        # Larger App Logo for Sidebar
        logo_p = config.ASSETS_DIR / "app_icon.png"
        if logo_p.exists():
            try:
                pil_logo = Image.open(logo_p)
                self.icons["app_logo"] = ctk.CTkImage(
                    light_image=pil_logo,
                    dark_image=pil_logo,
                    size=(36, 36)
                )
            except Exception:
                pass

    def get_icon(self, name: str) -> Optional[ctk.CTkImage]:
        return self.icons.get(name)

    # ── Layout Construction ──────────────────────────────────────────────────
    def _create_layout(self):
        # 2-Column Grid: Sidebar (Col 0) and Main Content (Col 1)
        self.grid_columnconfigure(0, weight=0, minsize=220)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──
        self.sidebar = ctk.CTkFrame(self, fg_color=self.C_SIDEBAR, corner_radius=0, width=220)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # App Brand Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(18, 20))

        if "app_logo" in self.icons:
            logo_lbl = ctk.CTkLabel(brand_frame, text="", image=self.icons["app_logo"])
            logo_lbl.pack(side="left", padx=(0, 10))

        title_box = ctk.CTkFrame(brand_frame, fg_color="transparent")
        title_box.pack(side="left", fill="both")
        lbl_brand = ctk.CTkLabel(
            title_box, text="MYTHORIA",
            font=get_font(16, "bold"), text_color=self.C_TEXT
        )
        lbl_brand.pack(anchor="w")
        lbl_sub = ctk.CTkLabel(
            title_box, text="SMP Chat Solver",
            font=get_font(10), text_color=self.C_ACCENT
        )
        lbl_sub.pack(anchor="w")

        # Separator
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=self.C_BORDER)
        sep.pack(fill="x", padx=14, pady=(0, 14))

        # Nav Buttons Container
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        self.nav_items = [
            ("dashboard", "Dashboard", "dashboard"),
            ("general", "General & MC", "settings"),
            ("solvers", "Solvers & Delays", "solvers"),
            ("stealth", "Stealth Anti-Cheat", "stealth"),
            ("tabchi", "Tabchi Auto-Ads", "tabchi"),
            ("sandbox", "Sandbox & Stats", "stats"),
        ]

        for tab_id, label, icon_key in self.nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {label}",
                image=self.get_icon(icon_key),
                compound="left",
                font=get_font(12, "bold"),
                anchor="w",
                height=42,
                corner_radius=8,
                fg_color="transparent",
                text_color=self.C_TEXT_MUTED,
                hover_color=self.C_CARD_HOVER,
                command=lambda tid=tab_id: self.switch_tab(tid),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self.nav_buttons[tab_id] = btn

        # Sidebar Footer: Bot Control Card
        sidebar_bottom = ctk.CTkFrame(self.sidebar, fg_color=self.C_CARD, corner_radius=10)
        sidebar_bottom.pack(side="bottom", fill="x", padx=12, pady=16)

        # Status Pill
        self.status_pill = ctk.CTkLabel(
            sidebar_bottom,
            text="● STOPPED",
            font=get_font(11, "bold"),
            text_color=self.C_DANGER,
        )
        self.status_pill.pack(pady=(10, 6))

        # Master Start / Stop Button
        self.btn_master_toggle = ctk.CTkButton(
            sidebar_bottom,
            text=" START BOT",
            image=self.get_icon("play"),
            compound="left",
            font=get_font(12, "bold"),
            fg_color=self.C_SUCCESS,
            hover_color="#16a34a",
            height=36,
            corner_radius=6,
            command=self.toggle_bot,
        )
        self.btn_master_toggle.pack(fill="x", padx=10, pady=(0, 10))

        # ── Main Content Area ──
        self.main_content = ctk.CTkFrame(self, fg_color=self.C_BG, corner_radius=0)
        self.main_content.grid(row=0, column=1, sticky="nsew")
        self.main_content.grid_rowconfigure(1, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)

        # Header Bar
        self._create_header_bar()

        # Tab Frames Stack Container
        self.tab_container = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tab_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.tab_container.grid_rowconfigure(0, weight=1)
        self.tab_container.grid_columnconfigure(0, weight=1)

        # Instantiate all tab views
        self.tab_frames: Dict[str, ctk.CTkFrame] = {}
        self._build_tab_dashboard()
        self._build_tab_general()
        self._build_tab_solvers()
        self._build_tab_stealth()
        self._build_tab_tabchi()
        self._build_tab_sandbox()

        # Initialize grid geometry for all tab views, keeping inactive tabs unmapped
        for tid, frame in self.tab_frames.items():
            frame.grid(row=0, column=0, sticky="nsew")
            if tid != "dashboard":
                frame.grid_remove()

        # Select initial tab
        self.current_tab = "dashboard"
        self.switch_tab("dashboard")

    # ── Header Bar ───────────────────────────────────────────────────────────
    def _create_header_bar(self):
        header = ctk.CTkFrame(self.main_content, fg_color="transparent", height=60)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 12))
        header.grid_columnconfigure(0, weight=1)

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w")

        self.lbl_page_title = ctk.CTkLabel(
            title_frame, text="Dashboard",
            font=get_font(20, "bold"), text_color=self.C_TEXT
        )
        self.lbl_page_title.pack(anchor="w")

        self.lbl_page_desc = ctk.CTkLabel(
            title_frame, text="Real-time chat game monitoring, answer dispatch & live telemetry",
            font=get_font(11), text_color=self.C_TEXT_MUTED
        )
        self.lbl_page_desc.pack(anchor="w")

        actions_frame = ctk.CTkFrame(header, fg_color="transparent")
        actions_frame.grid(row=0, column=1, sticky="e")

        self.lbl_save_status = ctk.CTkLabel(
            actions_frame, text="",
            font=get_font(11, "bold"), text_color=self.C_SUCCESS
        )
        self.lbl_save_status.pack(side="left", padx=(0, 10))

        btn_save = ctk.CTkButton(
            actions_frame,
            text=" SAVE SETTINGS",
            image=self.get_icon("save"),
            compound="left",
            font=get_font(12, "bold"),
            fg_color=self.C_ACCENT,
            hover_color=self.C_ACCENT_HOVER,
            text_color="#0f172a",
            height=36,
            corner_radius=6,
            command=self.save_all_settings,
        )
        btn_save.pack(side="left")

    # ── Tab Navigation (Silky Smooth Instant Switch) ──────────────────────────
    def switch_tab(self, tab_id: str):
        self.current_tab = tab_id

        # Update button highlights & icons
        for tid, btn in self.nav_buttons.items():
            icon_key = self.nav_icon_map.get(tid, tid)
            if tid == tab_id:
                btn.configure(
                    fg_color=self.C_CARD,
                    text_color=self.C_ACCENT,
                    image=self.get_icon(f"{icon_key}_active") or self.get_icon(icon_key)
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=self.C_TEXT_MUTED,
                    image=self.get_icon(icon_key)
                )

        # Instant 0ms visual switch: map target frame and unmap others cleanly
        for tid, frame in self.tab_frames.items():
            if tid == tab_id:
                frame.grid()
                actual_widget = getattr(frame, "_parent_frame", frame)
                actual_widget.tkraise()
            else:
                frame.grid_remove()

        # Update page title & description
        titles = {
            "dashboard": ("Dashboard & Live Monitor", "Live chat monitoring, candidate dispatch, and real-time event telemetry"),
            "general": ("General & Minecraft Settings", "Player account identity, Minecraft log selector, typing methods, and delays"),
            "solvers": ("Solvers & Game Delays", "Configure individual solver heuristics, response delays, and self-learning filters"),
            "stealth": ("Stealth & Anti-Cheat Evasion", "Human typo simulation, mistake injection, and anti-ban mechanics"),
            "tabchi": ("Tabchi / Auto-Advertiser", "Automated auction promotion, interval scheduling, and anti-duplicate dot bypass"),
            "sandbox": ("Interactive Sandbox & Statistics", "Direct puzzle solver testing playground and historical win rate analytics"),
        }
        t, d = titles.get(tab_id, ("Settings", ""))
        self.lbl_page_title.configure(text=t)
        self.lbl_page_desc.configure(text=d)

    # ── TAB 1: Dashboard ─────────────────────────────────────────────────────
    def _build_tab_dashboard(self):
        f = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self.tab_frames["dashboard"] = f
        f.grid_rowconfigure(2, weight=1)
        f.grid_columnconfigure(0, weight=1)

        # Top Stats Cards (4 horizontal)
        stats_frame = ctk.CTkFrame(f, fg_color="transparent")
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)

        self.card_games = self._create_stat_card(stats_frame, 0, "GAMES DETECTED", "0", self.C_ACCENT)
        self.card_wins = self._create_stat_card(stats_frame, 1, "GAMES WON", "0 (0%)", self.C_SUCCESS)
        self.card_accuracy = self._create_stat_card(stats_frame, 2, "BOT ACCURACY", "0.0%", self.C_WARNING)
        self.card_ads = self._create_stat_card(stats_frame, 3, "ADS SENT", "0", "#c084fc")

        # Control Bar
        ctrl_frame = ctk.CTkFrame(f, fg_color=self.C_CARD, corner_radius=8, height=48)
        ctrl_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        btn_start = ctk.CTkButton(
            ctrl_frame, text=" START MONITORING",
            image=self.get_icon("play"), compound="left",
            font=get_font(12, "bold"), fg_color=self.C_SUCCESS, hover_color="#16a34a",
            height=32, corner_radius=6, command=self.start_bot
        )
        btn_start.pack(side="left", padx=(12, 6), pady=8)

        btn_stop = ctk.CTkButton(
            ctrl_frame, text=" STOP",
            image=self.get_icon("stop"), compound="left",
            font=get_font(12, "bold"), fg_color=self.C_DANGER, hover_color="#dc2626",
            height=32, corner_radius=6, command=self.stop_bot
        )
        btn_stop.pack(side="left", padx=6, pady=8)

        btn_clear = ctk.CTkButton(
            ctrl_frame, text=" CLEAR LOGS",
            image=self.get_icon("trash"), compound="left",
            font=get_font(11, "bold"), fg_color="#334155", hover_color="#475569",
            height=32, corner_radius=6, command=self.clear_logs
        )
        btn_clear.pack(side="left", padx=6, pady=8)

        self.sw_replay = ctk.CTkSwitch(
            ctrl_frame, text="Replay Historical Log",
            font=get_font(11), progress_color=self.C_ACCENT
        )
        self.sw_replay.pack(side="right", padx=14, pady=8)

        # Terminal / Live Feed Textbox
        self.txt_log = ctk.CTkTextbox(
            f,
            fg_color="#0a0c10",
            text_color="#e2e8f0",
            font=get_font(11),
            corner_radius=8,
            border_width=1,
            border_color=self.C_BORDER,
            wrap="word",
        )
        self.txt_log.grid(row=2, column=0, sticky="nsew", pady=(0, 8))

        # Bottom Telemetry Bar
        self.telemetry_strip = ctk.CTkLabel(
            f,
            text=f"Active Player: {self.settings.player_username} | Log: {self.settings.get_active_log_path().name} | Config: %APPDATA%/MythoriaSolver",
            font=get_font(10), text_color=self.C_TEXT_MUTED, anchor="w"
        )
        self.telemetry_strip.grid(row=3, column=0, sticky="ew")

        # Initial Welcome Log Line
        self.append_log("INFO", "MythoriaSolver GUI initialized and ready.")

    def _create_stat_card(self, parent, col: int, title: str, value: str, color: str):
        card = ctk.CTkFrame(parent, fg_color=self.C_CARD, corner_radius=8, border_width=1, border_color=self.C_BORDER)
        card.grid(row=0, column=col, sticky="ew", padx=4)

        lbl_t = ctk.CTkLabel(card, text=title, font=get_font(10, "bold"), text_color=self.C_TEXT_MUTED)
        lbl_t.pack(anchor="w", padx=12, pady=(10, 2))

        lbl_v = ctk.CTkLabel(card, text=value, font=get_font(18, "bold"), text_color=color)
        lbl_v.pack(anchor="w", padx=12, pady=(0, 10))
        return lbl_v

    # ── TAB 2: General & Minecraft ───────────────────────────────────────────
    def _build_tab_general(self):
        scroll = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")
        self.tab_frames["general"] = scroll
        scroll.grid_columnconfigure(0, weight=1)

        # Section 1: Player Identity
        s1 = self._create_settings_section(scroll, "PLAYER IDENTITY", "Minecraft in-game identity for winner detection and chat targeting")
        self.ent_username = self._add_entry_row(s1, "Minecraft Username", "Exact in-game display name (case-sensitive)")

        # Section 2: Log File & Launcher
        s2 = self._create_settings_section(scroll, "MINECRAFT INSTALLATION & LOG FILE", "Specify or auto-detect active latest.log path across all Minecraft launchers")
        
        path_row = ctk.CTkFrame(s2, fg_color="transparent")
        path_row.pack(fill="x", padx=14, pady=6)
        lbl_p = ctk.CTkLabel(path_row, text="Active latest.log Path", font=get_font(11, "bold"), text_color=self.C_TEXT)
        lbl_p.pack(anchor="w")

        path_input_row = ctk.CTkFrame(path_row, fg_color="transparent")
        path_input_row.pack(fill="x", pady=(4, 0))
        path_input_row.grid_columnconfigure(0, weight=1)

        self.ent_log_path = ctk.CTkEntry(
            path_input_row, font=get_font(11), fg_color="#12151d",
            border_color=self.C_BORDER, height=34
        )
        self.ent_log_path.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        btn_browse = ctk.CTkButton(
            path_input_row, text="Browse", image=self.get_icon("folder"), compound="left",
            font=get_font(11, "bold"), fg_color="#334155", hover_color="#475569",
            width=90, height=34, command=self._browse_log_file
        )
        btn_browse.grid(row=0, column=1, padx=(0, 8))

        btn_detect = ctk.CTkButton(
            path_input_row, text="Auto-Detect", image=self.get_icon("refresh"), compound="left",
            font=get_font(11, "bold"), fg_color=self.C_ACCENT, hover_color=self.C_ACCENT_HOVER,
            text_color="#0f172a", width=120, height=34, command=self._open_instance_selector
        )
        btn_detect.grid(row=0, column=2)

        # Section 3: Keyboard & Interaction
        s3 = self._create_settings_section(scroll, "AUTOMATION & INPUT SIMULATION", "Control keyboard scan codes, focus verification, and typing behavior")
        self.sw_dry_run = self._add_switch_row(s3, "Dry-Run Mode (Simulation only, no physical keystrokes sent)")
        self.sw_require_focus = self._add_switch_row(s3, "Require Minecraft Window Focus (Prevents typing while alt-tabbed)")

        send_m_row = ctk.CTkFrame(s3, fg_color="transparent")
        send_m_row.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(send_m_row, text="Send Method", font=get_font(11, "bold")).pack(side="left")
        self.seg_send_method = ctk.CTkSegmentedButton(
            send_m_row, values=["paste", "write"],
            font=get_font(11, "bold"), selected_color=self.C_ACCENT, selected_hover_color=self.C_ACCENT_HOVER
        )
        self.seg_send_method.pack(side="right")

        self.ent_chat_key = self._add_entry_row(s3, "Chat Key", "Key used to open chat in Minecraft (default: 't')")
        self.ent_cooldown = self._add_entry_row(s3, "Server Cooldown (Seconds)", "Minimum delay between consecutive chat messages (server limit: 3.0s)")
        self.ent_open_delay = self._add_entry_row(s3, "Post Open Chat Delay (Seconds)", "Wait time between pressing chat key and typing answer (default: 0.25)")
        self.ent_type_delay = self._add_entry_row(s3, "Post Type Delay (Seconds)", "Wait time between typing answer and pressing Enter (default: 0.10)")
        self.ent_retries = self._add_entry_row(s3, "Max Candidate Retries", "How many backup candidates to attempt if first answer isn't accepted (default: 2)")

        # Section 4: Answering Policies
        s4 = self._create_settings_section(scroll, "ANSWERING FREQUENCY & NUMBER STRATEGY", "Configure ratio of games answered and number guessing modes")
        self.ent_ratio = self._add_entry_row(s4, "Answer Ratio", "Answer 1 of every N games (1 = answer 100%, 2 = answer 50%, 3 = answer 33%)")

        gn_row = ctk.CTkFrame(s4, fg_color="transparent")
        gn_row.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(gn_row, text="Guess Number Strategy", font=get_font(11, "bold")).pack(side="left")
        self.seg_guess_mode = ctk.CTkSegmentedButton(
            gn_row, values=["random", "skip"],
            font=get_font(11, "bold"), selected_color=self.C_ACCENT, selected_hover_color=self.C_ACCENT_HOVER
        )
        self.seg_guess_mode.pack(side="right")

    # ── TAB 3: Solvers & Delays ──────────────────────────────────────────────
    def _build_tab_solvers(self):
        scroll = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")
        self.tab_frames["solvers"] = scroll
        scroll.grid_columnconfigure(0, weight=1)

        # Global Fallback Delays
        s_glob = self._create_settings_section(scroll, "GLOBAL FALLBACK DELAYS", "Used when a game type does not have specific delay overrides")
        self.ent_glob_min = self._add_entry_row(s_glob, "Global Min Delay (Seconds)", "Minimum human wait time before submitting")
        self.ent_glob_max = self._add_entry_row(s_glob, "Global Max Delay (Seconds)", "Maximum human wait time before submitting")

        # 7 Solvers Configuration
        s_solvers = self._create_settings_section(scroll, "SOLVER ENGINES & PER-TYPE DELAYS", "Enable/disable specific solvers and configure customized response delays")

        self.solver_widgets: Dict[str, Dict[str, Any]] = {}

        for gt in GAME_TYPES:
            card = ctk.CTkFrame(s_solvers, fg_color="#12151d", corner_radius=6, border_width=1, border_color=self.C_BORDER)
            card.pack(fill="x", padx=14, pady=6)
            card.grid_columnconfigure(1, weight=1)

            sw = ctk.CTkSwitch(
                card, text=f"  {GAME_TYPE_LABELS.get(gt, gt)}",
                font=get_font(12, "bold"), progress_color=self.C_SUCCESS
            )
            sw.grid(row=0, column=0, padx=12, pady=10, sticky="w")

            delays_frame = ctk.CTkFrame(card, fg_color="transparent")
            delays_frame.grid(row=0, column=1, padx=12, pady=6, sticky="e")

            ctk.CTkLabel(delays_frame, text="Min (s):", font=get_font(11)).pack(side="left", padx=4)
            ent_min = ctk.CTkEntry(delays_frame, width=64, height=28, font=get_font(11))
            ent_min.pack(side="left", padx=(0, 10))

            ctk.CTkLabel(delays_frame, text="Max (s):", font=get_font(11)).pack(side="left", padx=4)
            ent_max = ctk.CTkEntry(delays_frame, width=64, height=28, font=get_font(11))
            ent_max.pack(side="left")

            self.solver_widgets[gt] = {
                "switch": sw,
                "min": ent_min,
                "max": ent_max,
            }

        # Self-Learning Engine
        s_learn = self._create_settings_section(scroll, "AUTO-LEARNING ENGINE", "Automatically learn new Minecraft words and trivia answers announced in chat")
        self.sw_auto_learn = self._add_switch_row(s_learn, "Auto-Learn New Words from Game Winner Announcements")
        self.ent_learn_min_len = self._add_entry_row(s_learn, "Min Word Length", "Ignore answers shorter than this length (default: 3)")
        self.sw_filter_random = self._add_switch_row(s_learn, "Filter Random String Noise (Prevents memorizing anti-bot gibberish like 'zK9xP')")

    # ── TAB 4: Stealth & Anti-Cheat ──────────────────────────────────────────
    def _build_tab_stealth(self):
        scroll = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")
        self.tab_frames["stealth"] = scroll
        scroll.grid_columnconfigure(0, weight=1)

        s_stealth = self._create_settings_section(
            scroll, "HUMAN MISTAKE SIMULATION",
            "Deliberately sends 0-2 plausible wrong attempts before typing the correct answer to bypass anti-cheat heuristics"
        )
        self.ent_fake_min = self._add_entry_row(s_stealth, "Min Wrong Attempts", "Minimum fake typos to submit (0 = sometimes answers directly)")
        self.ent_fake_max = self._add_entry_row(s_stealth, "Max Wrong Attempts", "Maximum fake typos before submitting correct answer (0 = disabled)")
        self.ent_fake_cooldown = self._add_entry_row(s_stealth, "Fake Attempt Cooldown (Seconds)", "Delay between fake wrong attempts (server cooldown: 3.0s)")

        s_patterns = self._create_settings_section(
            scroll, "TYPO GENERATION PATTERNS",
            "Choose which real-world human mistake types to simulate"
        )
        self.sw_typo_keys = self._add_switch_row(s_patterns, "Keyboard Neighbor Typos (Accidental slip on adjacent QWERTY key)")
        self.sw_typo_case = self._add_switch_row(s_patterns, "Initial Swap Case (Starts with lowercase when uppercase expected)")
        self.sw_typo_part = self._add_switch_row(s_patterns, "Partial Word Submissions (Submits unfinished prefix before correcting)")
        self.sw_typo_rev = self._add_switch_row(s_patterns, "Reversed Word Submissions (Inverts characters accidentally)")
        self.sw_typo_miss = self._add_switch_row(s_patterns, "Missing Characters (Drops random letter as if in a rush)")

    # ── TAB 5: Tabchi / Auto-Advertiser ──────────────────────────────────────
    def _build_tab_tabchi(self):
        scroll = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")
        self.tab_frames["tabchi"] = scroll
        scroll.grid_columnconfigure(0, weight=1)

        s_master = self._create_settings_section(scroll, "AUTO-ADVERTISER ACTIVATION", "Periodically promote your items, auction listings, or custom chat messages")
        self.sw_tabchi_enabled = self._add_switch_row(s_master, "Enable Tabchi Auto-Advertiser (تبچی)")

        s_timing = self._create_settings_section(scroll, "INTERVAL & TIMING SCHEDULE", "Specify delivery frequencies in minutes")
        self.ent_tabchi_min = self._add_entry_row(s_timing, "Min Interval (Minutes)", "Shortest wait time before sending next advertisement")
        self.ent_tabchi_max = self._add_entry_row(s_timing, "Max Interval (Minutes)", "Longest wait time before sending next advertisement")
        self.sw_tabchi_random = self._add_switch_row(s_timing, "Randomize Interval Between Min and Max (Evades spam timers)")

        s_dispatch = self._create_settings_section(scroll, "DISPATCH RULES & DUPLICATE BYPASS", "Order and server anti-spam filter evasion")

        order_row = ctk.CTkFrame(s_dispatch, fg_color="transparent")
        order_row.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(order_row, text="Message Selection Order", font=get_font(11, "bold")).pack(side="left")
        self.seg_tabchi_order = ctk.CTkSegmentedButton(
            order_row, values=["cycle", "random"],
            font=get_font(11, "bold"), selected_color=self.C_ACCENT, selected_hover_color=self.C_ACCENT_HOVER
        )
        self.seg_tabchi_order.pack(side="right")

        self.sw_tabchi_dot = self._add_switch_row(s_dispatch, "Anti-Duplicate Dot Bypass (Sends '.' before advert to evade server duplicate block)")
        self.ent_tabchi_dot_delay = self._add_entry_row(s_dispatch, "Dot Cooldown Delay (Seconds)", "Wait time between the dot and the actual message")

        # Message List Manager
        s_msgs = self._create_settings_section(scroll, "ADVERTISEMENT MESSAGE POOL", "Manage the pool of messages rotated by the auto-advertiser")

        # Input to add new message
        add_frame = ctk.CTkFrame(s_msgs, fg_color="transparent")
        add_frame.pack(fill="x", padx=14, pady=(6, 10))
        add_frame.grid_columnconfigure(0, weight=1)

        self.ent_new_ad = ctk.CTkEntry(
            add_frame, placeholder_text="Enter new advertisement message (/ah view ...)...",
            font=get_font(11), height=34, fg_color="#12151d", border_color=self.C_BORDER
        )
        self.ent_new_ad.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        btn_add_ad = ctk.CTkButton(
            add_frame, text="Add", image=self.get_icon("plus"), compound="left",
            font=get_font(11, "bold"), fg_color=self.C_SUCCESS, hover_color="#16a34a",
            width=80, height=34, command=self._add_advert_message
        )
        btn_add_ad.grid(row=0, column=1)

        # Messages listbox container
        self.ad_list_frame = ctk.CTkScrollableFrame(
            s_msgs, fg_color="#12151d", height=180, corner_radius=6,
            border_width=1, border_color=self.C_BORDER
        )
        self.ad_list_frame.pack(fill="x", padx=14, pady=(0, 10))
        self.ad_list_frame.grid_columnconfigure(0, weight=1)

        # Toolbar under messages list
        list_toolbar = ctk.CTkFrame(s_msgs, fg_color="transparent")
        list_toolbar.pack(fill="x", padx=14, pady=(0, 6))

        btn_reset_ads = ctk.CTkButton(
            list_toolbar, text="Reset Defaults", font=get_font(11),
            fg_color="#334155", hover_color="#475569", width=120, height=30,
            command=self._reset_default_adverts
        )
        btn_reset_ads.pack(side="left")

        self.lbl_ad_count = ctk.CTkLabel(list_toolbar, text="", font=get_font(11), text_color=self.C_TEXT_MUTED)
        self.lbl_ad_count.pack(side="right")

    # ── TAB 6: Sandbox & Stats ───────────────────────────────────────────────
    def _build_tab_sandbox(self):
        scroll = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")
        self.tab_frames["sandbox"] = scroll
        scroll.grid_columnconfigure(0, weight=1)

        # Solver Sandbox
        s_box = self._create_settings_section(scroll, "INSTANT SOLVER SANDBOX", "Test any chat game puzzle or math expression with live solver verification")

        test_row = ctk.CTkFrame(s_box, fg_color="transparent")
        test_row.pack(fill="x", padx=14, pady=8)
        test_row.grid_columnconfigure(0, weight=1)

        self.ent_sandbox_input = ctk.CTkEntry(
            test_row, placeholder_text="e.g. 'c_w' or 'e e p r e c r' or '24 * (5 + 3)' or '1-50'...",
            font=get_font(12), height=38, fg_color="#12151d", border_color=self.C_BORDER
        )
        self.ent_sandbox_input.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.ent_sandbox_input.bind("<Return>", lambda e: self._test_solve_sandbox())

        self.opt_sandbox_type = ctk.CTkOptionMenu(
            test_row,
            values=["Auto-Detect"] + [GAME_TYPE_LABELS.get(gt, gt) for gt in GAME_TYPES],
            font=get_font(11, "bold"), fg_color="#334155", button_color="#475569",
            height=38, width=170
        )
        self.opt_sandbox_type.grid(row=0, column=1, padx=(0, 8))

        btn_solve = ctk.CTkButton(
            test_row, text=" SOLVE", image=self.get_icon("bolt"), compound="left",
            font=get_font(12, "bold"), fg_color=self.C_ACCENT, hover_color=self.C_ACCENT_HOVER,
            text_color="#0f172a", height=38, width=100, command=self._test_solve_sandbox
        )
        btn_solve.grid(row=0, column=2)

        # Sandbox Result Card
        self.sandbox_result_card = ctk.CTkFrame(s_box, fg_color="#12151d", corner_radius=6, border_width=1, border_color=self.C_BORDER)
        self.sandbox_result_card.pack(fill="x", padx=14, pady=(0, 10))

        self.lbl_sandbox_output = ctk.CTkLabel(
            self.sandbox_result_card, text="Enter a puzzle question above and click Solve.",
            font=get_font(11), text_color=self.C_TEXT_MUTED, justify="left", anchor="w"
        )
        self.lbl_sandbox_output.pack(fill="x", padx=14, pady=12)

        # Database & Historical Analytics
        s_db = self._create_settings_section(scroll, "DATABASE & HISTORICAL PERFORMANCE", "Local database item count and persistent session statistics")

        db_info_frame = ctk.CTkFrame(s_db, fg_color="transparent")
        db_info_frame.pack(fill="x", padx=14, pady=8)

        total_db_items = len(self.db.all_items)
        lbl_db_items = ctk.CTkLabel(
            db_info_frame, text=f"• Verified Database Items: {total_db_items:,} Minecraft blocks/items/mobs",
            font=get_font(12, "bold"), text_color=self.C_TEXT
        )
        lbl_db_items.pack(anchor="w", pady=2)

        settings_path_lbl = ctk.CTkLabel(
            db_info_frame, text=f"• Persistent Settings Path: {SETTINGS_FILE}",
            font=get_font(11), text_color=self.C_ACCENT
        )
        settings_path_lbl.pack(anchor="w", pady=2)

        db_path_lbl = ctk.CTkLabel(
            db_info_frame, text=f"• Database Path: {config.DB_PATH}",
            font=get_font(11), text_color=self.C_TEXT_MUTED
        )
        db_path_lbl.pack(anchor="w", pady=2)

        # Historical Collector Stats
        hist_stats = self.bot_instance.collector.get_stats() if self.bot_instance else {}
        if not hist_stats:
            from collector.chat_game_collector import ChatGameCollector
            c = ChatGameCollector()
            hist_stats = c.get_stats()

        stats_box = ctk.CTkFrame(s_db, fg_color="#12151d", corner_radius=6, border_width=1, border_color=self.C_BORDER)
        stats_box.pack(fill="x", padx=14, pady=(6, 12))

        hist_text = (
            f"All-Time Logged Games: {hist_stats.get('total_games', 0)}  |  "
            f"Bot Won: {hist_stats.get('won_games', 0)} ({hist_stats.get('win_rate_pct', 0.0)}%)  |  "
            f"Correct Answers: {hist_stats.get('correct_answers', 0)} ({hist_stats.get('accuracy_pct', 0.0)}%)"
        )
        lbl_h = ctk.CTkLabel(stats_box, text=hist_text, font=get_font(11, "bold"), text_color=self.C_SUCCESS)
        lbl_h.pack(padx=12, pady=10)

    # ── UI Builder Helpers ───────────────────────────────────────────────────
    def _create_settings_section(self, parent, title: str, subtitle: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color=self.C_CARD, corner_radius=8, border_width=1, border_color=self.C_BORDER)
        card.pack(fill="x", pady=(0, 14))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(12, 6))

        ctk.CTkLabel(hdr, text=title, font=get_font(13, "bold"), text_color=self.C_TEXT).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(hdr, text=subtitle, font=get_font(10), text_color=self.C_TEXT_MUTED).pack(anchor="w")

        sep = ctk.CTkFrame(card, height=1, fg_color=self.C_BORDER)
        sep.pack(fill="x", padx=14, pady=(4, 6))
        return card

    def _add_entry_row(self, parent, label: str, tooltip: str = "") -> ctk.CTkEntry:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=5)
        row.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(row, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(title_box, text=label, font=get_font(11, "bold"), text_color=self.C_TEXT).pack(anchor="w")
        if tooltip:
            ctk.CTkLabel(title_box, text=tooltip, font=get_font(10), text_color=self.C_TEXT_MUTED).pack(anchor="w")

        ent = ctk.CTkEntry(row, width=200, height=32, font=get_font(11), fg_color="#12151d", border_color=self.C_BORDER)
        ent.grid(row=0, column=1, sticky="e")
        return ent

    def _add_switch_row(self, parent, label: str) -> ctk.CTkSwitch:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=5)
        sw = ctk.CTkSwitch(row, text=f"  {label}", font=get_font(11), progress_color=self.C_SUCCESS)
        sw.pack(anchor="w")
        return sw

    # ── Populate Settings into UI ────────────────────────────────────────────
    def _populate_all_settings(self):
        s = self.settings

        # General
        self.ent_username.delete(0, "end")
        self.ent_username.insert(0, s.player_username)

        self.ent_log_path.delete(0, "end")
        self.ent_log_path.insert(0, s.minecraft_log_path)

        if s.dry_run:
            self.sw_dry_run.select()
        else:
            self.sw_dry_run.deselect()

        if s.require_focus:
            self.sw_require_focus.select()
        else:
            self.sw_require_focus.deselect()

        self.seg_send_method.set(s.send_method)

        self.ent_chat_key.delete(0, "end")
        self.ent_chat_key.insert(0, s.chat_key)

        self.ent_cooldown.delete(0, "end")
        self.ent_cooldown.insert(0, str(s.send_cooldown))

        self.ent_open_delay.delete(0, "end")
        self.ent_open_delay.insert(0, str(getattr(s, "post_open_chat_delay", 0.25)))

        self.ent_type_delay.delete(0, "end")
        self.ent_type_delay.insert(0, str(getattr(s, "post_type_delay", 0.10)))

        self.ent_retries.delete(0, "end")
        self.ent_retries.insert(0, str(s.max_candidate_retries))

        self.ent_ratio.delete(0, "end")
        self.ent_ratio.insert(0, str(s.answer_ratio))

        self.seg_guess_mode.set(s.guess_number_mode)

        # Global Delays
        self.ent_glob_min.delete(0, "end")
        self.ent_glob_min.insert(0, str(s.global_min_delay))
        self.ent_glob_max.delete(0, "end")
        self.ent_glob_max.insert(0, str(s.global_max_delay))

        # Per-Game Solvers
        for gt, widgets in self.solver_widgets.items():
            gd = s.game_delays.get(gt, GameTypeDelay())
            if gd.enabled:
                widgets["switch"].select()
            else:
                widgets["switch"].deselect()

            widgets["min"].delete(0, "end")
            widgets["min"].insert(0, str(gd.min_delay))

            widgets["max"].delete(0, "end")
            widgets["max"].insert(0, str(gd.max_delay))

        # Auto-Learn
        if s.auto_learn_words:
            self.sw_auto_learn.select()
        else:
            self.sw_auto_learn.deselect()

        self.ent_learn_min_len.delete(0, "end")
        self.ent_learn_min_len.insert(0, str(s.auto_learn_min_length))

        if s.auto_learn_filter_random:
            self.sw_filter_random.select()
        else:
            self.sw_filter_random.deselect()

        # Stealth
        st = s.stealth
        self.ent_fake_min.delete(0, "end")
        self.ent_fake_min.insert(0, str(st.fake_attempts_min))

        self.ent_fake_max.delete(0, "end")
        self.ent_fake_max.insert(0, str(st.fake_attempts_max))

        self.ent_fake_cooldown.delete(0, "end")
        self.ent_fake_cooldown.insert(0, str(st.fake_attempt_cooldown))

        if st.typo_nearby_keys:
            self.sw_typo_keys.select()
        else:
            self.sw_typo_keys.deselect()

        if st.typo_swap_case:
            self.sw_typo_case.select()
        else:
            self.sw_typo_case.deselect()

        if st.typo_partial_word:
            self.sw_typo_part.select()
        else:
            self.sw_typo_part.deselect()

        if st.typo_reversed_word:
            self.sw_typo_rev.select()
        else:
            self.sw_typo_rev.deselect()

        if st.typo_missing_chars:
            self.sw_typo_miss.select()
        else:
            self.sw_typo_miss.deselect()

        # Tabchi
        tab = s.tabchi
        if tab.enabled:
            self.sw_tabchi_enabled.select()
        else:
            self.sw_tabchi_enabled.deselect()

        self.ent_tabchi_min.delete(0, "end")
        self.ent_tabchi_min.insert(0, str(tab.min_interval_minutes))

        self.ent_tabchi_max.delete(0, "end")
        self.ent_tabchi_max.insert(0, str(tab.max_interval_minutes))

        if tab.randomize_interval:
            self.sw_tabchi_random.select()
        else:
            self.sw_tabchi_random.deselect()

        self.seg_tabchi_order.set(tab.order)

        if tab.anti_duplicate_dot:
            self.sw_tabchi_dot.select()
        else:
            self.sw_tabchi_dot.deselect()

        self.ent_tabchi_dot_delay.delete(0, "end")
        self.ent_tabchi_dot_delay.insert(0, str(tab.dot_delay_seconds))

        self._refresh_advert_list_ui()

    # ── Read Settings From UI ────────────────────────────────────────────────
    def _collect_settings_from_ui(self):
        s = self.settings

        # General
        s.player_username = self.ent_username.get().strip() or "Player"
        s.minecraft_log_path = self.ent_log_path.get().strip()
        s.dry_run = bool(self.sw_dry_run.get())
        s.require_focus = bool(self.sw_require_focus.get())
        s.send_method = self.seg_send_method.get()
        s.chat_key = self.ent_chat_key.get().strip() or "t"

        try:
            s.send_cooldown = float(self.ent_cooldown.get())
        except ValueError:
            s.send_cooldown = 3.0

        try:
            s.post_open_chat_delay = float(self.ent_open_delay.get())
        except ValueError:
            s.post_open_chat_delay = 0.25

        try:
            s.post_type_delay = float(self.ent_type_delay.get())
        except ValueError:
            s.post_type_delay = 0.10

        try:
            s.max_candidate_retries = int(self.ent_retries.get())
        except ValueError:
            s.max_candidate_retries = 2

        try:
            s.answer_ratio = max(1, int(self.ent_ratio.get()))
        except ValueError:
            s.answer_ratio = 1

        s.guess_number_mode = self.seg_guess_mode.get()

        # Delays
        try:
            s.global_min_delay = float(self.ent_glob_min.get())
            s.global_max_delay = float(self.ent_glob_max.get())
        except ValueError:
            s.global_min_delay = 3.0
            s.global_max_delay = 7.0

        for gt, widgets in self.solver_widgets.items():
            en = bool(widgets["switch"].get())
            try:
                mn = float(widgets["min"].get())
                mx = float(widgets["max"].get())
            except ValueError:
                mn, mx = 3.0, 7.0
            s.game_delays[gt] = GameTypeDelay(min_delay=mn, max_delay=mx, enabled=en)

        # Auto-Learn
        s.auto_learn_words = bool(self.sw_auto_learn.get())
        try:
            s.auto_learn_min_length = int(self.ent_learn_min_len.get())
        except ValueError:
            s.auto_learn_min_length = 3
        s.auto_learn_filter_random = bool(self.sw_filter_random.get())

        # Stealth
        try:
            s.stealth.fake_attempts_min = int(self.ent_fake_min.get())
            s.stealth.fake_attempts_max = int(self.ent_fake_max.get())
            s.stealth.fake_attempt_cooldown = float(self.ent_fake_cooldown.get())
        except ValueError:
            pass

        s.stealth.typo_nearby_keys = bool(self.sw_typo_keys.get())
        s.stealth.typo_swap_case = bool(self.sw_typo_case.get())
        s.stealth.typo_partial_word = bool(self.sw_typo_part.get())
        s.stealth.typo_reversed_word = bool(self.sw_typo_rev.get())
        s.stealth.typo_missing_chars = bool(self.sw_typo_miss.get())

        # Tabchi
        s.tabchi.enabled = bool(self.sw_tabchi_enabled.get())
        try:
            s.tabchi.min_interval_minutes = float(self.ent_tabchi_min.get())
            s.tabchi.max_interval_minutes = float(self.ent_tabchi_max.get())
            s.tabchi.dot_delay_seconds = float(self.ent_tabchi_dot_delay.get())
        except ValueError:
            pass
        s.tabchi.randomize_interval = bool(self.sw_tabchi_random.get())
        s.tabchi.order = self.seg_tabchi_order.get()
        s.tabchi.anti_duplicate_dot = bool(self.sw_tabchi_dot.get())

    def save_all_settings(self):
        """Save settings to %APPDATA%/MythoriaSolver/settings.json and provide UI feedback."""
        self._collect_settings_from_ui()
        self.settings.save()

        # Update telemetry strip
        active_p = self.settings.get_active_log_path()
        self.telemetry_strip.configure(
            text=f"Active Player: {self.settings.player_username} | Log: {active_p.name} | Config: %APPDATA%/MythoriaSolver/settings.json"
        )

        self.lbl_save_status.configure(text="Settings Saved ✓")
        self.append_log("INFO", f"Settings saved to {SETTINGS_FILE}")

        # Clear feedback after 2.5s
        self.after(2500, lambda: self.lbl_save_status.configure(text=""))

    # ── Minecraft Launcher Auto-Detector Dialog ──────────────────────────────
    def _browse_log_file(self):
        initial = os.path.expandvars(r"%APPDATA%\.minecraft\logs")
        path = filedialog.askopenfilename(
            title="Select Minecraft latest.log",
            initialdir=initial if os.path.exists(initial) else None,
            filetypes=[("Minecraft Log", "latest.log"), ("Log Files", "*.log"), ("All Files", "*.*")]
        )
        if path:
            self.ent_log_path.delete(0, "end")
            self.ent_log_path.insert(0, path)

    def _open_instance_selector(self):
        """Discovers all installed Minecraft launchers and lets user pick with 1 click."""
        instances = detect_minecraft_logs(custom_path=self.ent_log_path.get())
        if not instances:
            messagebox.showinfo("Auto-Detect", "No standard Minecraft installations found on this system.")
            return

        top = ctk.CTkToplevel(self)
        top.title("Auto-Detected Minecraft Versions")
        top.geometry("640x480")
        top.transient(self)
        top.grab_set()

        lbl = ctk.CTkLabel(
            top, text="Select Installed Minecraft Instance:",
            font=get_font(14, "bold"), text_color=self.C_TEXT
        )
        lbl.pack(padx=16, pady=(16, 8), anchor="w")

        sub = ctk.CTkLabel(
            top, text="Sorted by most recently modified logs. Click 'Select' to use.",
            font=get_font(11), text_color=self.C_TEXT_MUTED
        )
        sub.pack(padx=16, pady=(0, 10), anchor="w")

        sf = ctk.CTkScrollableFrame(top, fg_color="#12151d", border_width=1, border_color=self.C_BORDER)
        sf.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        sf.grid_columnconfigure(0, weight=1)

        for idx, inst in enumerate(instances):
            row = ctk.CTkFrame(sf, fg_color=self.C_CARD, corner_radius=6)
            row.pack(fill="x", pady=4, padx=4)
            row.grid_columnconfigure(0, weight=1)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.grid(row=0, column=0, sticky="w", padx=10, pady=8)

            name_lbl = ctk.CTkLabel(info, text=inst.name, font=get_font(12, "bold"), text_color=self.C_ACCENT)
            name_lbl.pack(anchor="w")

            detail_lbl = ctk.CTkLabel(
                info, text=f"Last modified: {inst.formatted_mtime} | {inst.path}",
                font=get_font(10), text_color=self.C_TEXT_MUTED
            )
            detail_lbl.pack(anchor="w")

            def choose_instance(p=inst.path):
                self.ent_log_path.delete(0, "end")
                self.ent_log_path.insert(0, str(p.resolve()))
                top.destroy()
                self.save_all_settings()

            btn = ctk.CTkButton(
                row, text="Select", width=70, height=28,
                font=get_font(11, "bold"), fg_color=self.C_SUCCESS, hover_color="#16a34a",
                command=choose_instance
            )
            btn.grid(row=0, column=1, padx=10, pady=8)

    # ── Tabchi Messages UI ───────────────────────────────────────────────────
    def _refresh_advert_list_ui(self):
        for widget in self.ad_list_frame.winfo_children():
            widget.destroy()

        msgs = self.settings.tabchi.messages
        self.lbl_ad_count.configure(text=f"Total: {len(msgs)} messages")

        if not msgs:
            lbl = ctk.CTkLabel(self.ad_list_frame, text="No advertisements configured.", font=get_font(11), text_color=self.C_TEXT_MUTED)
            lbl.pack(padx=10, pady=10)
            return

        for idx, msg in enumerate(msgs):
            item = ctk.CTkFrame(self.ad_list_frame, fg_color=self.C_CARD, corner_radius=4)
            item.pack(fill="x", pady=2, padx=4)
            item.grid_columnconfigure(1, weight=1)

            num_lbl = ctk.CTkLabel(item, text=f"#{idx+1}", font=get_font(10, "bold"), text_color=self.C_ACCENT, width=32)
            num_lbl.grid(row=0, column=0, padx=(8, 4), pady=4)

            text_lbl = ctk.CTkLabel(item, text=msg, font=get_font(11), text_color=self.C_TEXT, anchor="w")
            text_lbl.grid(row=0, column=1, sticky="w", padx=4, pady=4)

            def del_msg(i=idx):
                if 0 <= i < len(self.settings.tabchi.messages):
                    self.settings.tabchi.messages.pop(i)
                    self._refresh_advert_list_ui()

            btn_del = ctk.CTkButton(
                item, text="✕", width=24, height=24, font=get_font(10, "bold"),
                fg_color="transparent", hover_color=self.C_DANGER, text_color=self.C_DANGER,
                command=del_msg
            )
            btn_del.grid(row=0, column=2, padx=6, pady=4)

    def _add_advert_message(self):
        new_text = self.ent_new_ad.get().strip()
        if new_text:
            self.settings.tabchi.messages.append(new_text)
            self.ent_new_ad.delete(0, "end")
            self._refresh_advert_list_ui()

    def _reset_default_adverts(self):
        self.settings.tabchi.messages = list(DEFAULT_TABCHI_MESSAGES)
        self._refresh_advert_list_ui()

    # ── Interactive Sandbox ──────────────────────────────────────────────────
    def _test_solve_sandbox(self):
        raw_q = self.ent_sandbox_input.get().strip()
        if not raw_q:
            return

        sel_type = self.opt_sandbox_type.get()
        game_type = "auto"
        for gt, lbl in GAME_TYPE_LABELS.items():
            if lbl == sel_type:
                game_type = gt
                break

        t0 = time.perf_counter()
        detected = self.router.detect_type(game_type, raw_q)
        candidates = self.router.solve(game_type, raw_q)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        if not candidates:
            res_str = f"Type: {detected} | Solved in {elapsed_ms:.2f} ms\nResult: [X] No candidates found."
            self.lbl_sandbox_output.configure(text=res_str, text_color=self.C_DANGER)
            return

        lines = [
            f"Detected Type: {GAME_TYPE_LABELS.get(detected, detected)}  |  Solve Time: {elapsed_ms:.2f} ms",
            "Top Candidates:",
        ]
        for i, c in enumerate(candidates[:5], 1):
            lines.append(f"  [{i}] {c['answer']}  (Score: {c['score']:.1f} | Solver: {c.get('solver', 'N/A')})")

        self.lbl_sandbox_output.configure(text="\n".join(lines), text_color=self.C_SUCCESS)

    # ── Bot Thread & Event Dispatch ──────────────────────────────────────────
    def toggle_bot(self):
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()

    def start_bot(self):
        if self.is_running:
            return

        # Save settings first
        self.save_all_settings()

        replay_active = bool(self.sw_replay.get())

        self.is_running = True
        self.status_pill.configure(text="● RUNNING", text_color=self.C_SUCCESS)
        self.btn_master_toggle.configure(text=" STOP BOT", fg_color=self.C_DANGER, hover_color="#dc2626", image=self.get_icon("stop"))

        # Event bridge callback
        def on_event(event_type: str, data: Dict[str, Any]):
            self.event_queue.put((event_type, data))

        from main import MinecraftChatBot
        self.bot_instance = MinecraftChatBot(
            settings=self.settings,
            log_path=self.settings.get_active_log_path(),
            replay=replay_active,
            event_callback=on_event,
        )

        def runner():
            try:
                self.bot_instance.run()
            except Exception as e:
                self.event_queue.put(("error", {"error": str(e)}))
            finally:
                self.event_queue.put(("stopped", {}))

        self.bot_thread = threading.Thread(target=runner, daemon=True)
        self.bot_thread.start()

        self.append_log("INFO", f"Bot started monitoring: {self.settings.get_active_log_path().name}")

    def stop_bot(self):
        if not self.is_running:
            return

        self.is_running = False
        self.status_pill.configure(text="● STOPPED", text_color=self.C_DANGER)
        self.btn_master_toggle.configure(text=" START BOT", fg_color=self.C_SUCCESS, hover_color="#16a34a", image=self.get_icon("play"))

        if self.bot_instance:
            self.bot_instance.stop()

        self.append_log("INFO", "Bot stopped.")

    # ── Real-Time Event Queue Processor ──────────────────────────────────────
    def _process_event_queue(self):
        while not self.event_queue.empty():
            try:
                event_type, data = self.event_queue.get_nowait()
                self._handle_bot_event(event_type, data)
            except queue.Empty:
                break
            except Exception:
                pass

        self.after(50, self._process_event_queue)

    def _handle_bot_event(self, event_type: str, data: Dict[str, Any]):
        if event_type == "started":
            self.append_log("INFO", f"Log reader tailing: {data.get('log_path')}")

        elif event_type == "stopped":
            self.is_running = False
            self.status_pill.configure(text="● STOPPED", text_color=self.C_DANGER)
            self.btn_master_toggle.configure(text=" START BOT", fg_color=self.C_SUCCESS, hover_color="#16a34a", image=self.get_icon("play"))

        elif event_type == "question":
            self.stats_games += 1
            self.card_games.configure(text=str(self.stats_games))

            gn = data.get("game_number", 0)
            raw_t = data.get("raw_type", "")
            q = data.get("clean_question", "")
            det = data.get("detected_type", "")

            self.append_log("GAME", f"[GAME #{gn}] Type: {raw_t} ({det})")
            self.append_log("QUESTION", f"  Question: '{q}'")

        elif event_type == "candidates":
            cands = data.get("candidates", [])
            t_ms = data.get("solve_time_ms", 0.0)
            top = cands[0]["answer"] if cands else "None"
            self.append_log("SOLVER", f"  Top Candidate: '{top}' (Solved in {t_ms:.1f}ms)")

        elif event_type == "skipped":
            reason = data.get("reason", "")
            self.append_log("WARN", f"  [SKIPPED] {reason}")

        elif event_type == "fake_sent":
            fake = data.get("fake_msg", "")
            idx = data.get("index", 1)
            tot = data.get("total", 1)
            self.append_log("STEALTH", f"  [FAKE #{idx}/{tot}] Sent typo: '{fake}'")

        elif event_type == "answer_sent":
            ans = data.get("answer", "")
            dly = data.get("delay", 0.0)
            retry = data.get("is_retry", False)
            tag = "RETRY" if retry else "TYPED"
            self.append_log("ANSWER", f"  [{tag}] Submitted: '{ans}' (Delay: {dly:.2f}s)")

        elif event_type == "number_guessed":
            num = data.get("number", "")
            rem = data.get("remaining", 0)
            self.append_log("ANSWER", f"  [NUMBER GUESS] '{num}' ({rem} remaining in pool)")

        elif event_type == "game_ended":
            winner = data.get("winner", "Unknown")
            ans = data.get("answer", "")
            our_won = data.get("our_won", False)
            dur = data.get("duration")
            dur_str = f" in {dur:.2f}s" if dur else ""

            if our_won:
                self.stats_wins += 1
                self.append_log("WINNER", f"★ OUR BOT WON THE GAME! Answer was: '{ans}'{dur_str}")
            else:
                self.append_log("INFO", f"Game Ended. Winner: {winner} | Answer: '{ans}'{dur_str}")

            win_pct = (self.stats_wins / self.stats_games * 100) if self.stats_games > 0 else 0
            self.card_wins.configure(text=f"{self.stats_wins} ({win_pct:.0f}%)")

        elif event_type == "learned_word":
            w = data.get("word", "")
            self.append_log("LEARN", f"  + Learned new word added to DB: '{w}'")

        elif event_type == "learned_trivia":
            q = data.get("question", "")
            a = data.get("answer", "")
            self.append_log("LEARN", f"  + Learned trivia Q&A: '{q}' -> '{a}'")

        elif event_type == "advert_sent":
            self.stats_ads += 1
            self.card_ads.configure(text=str(self.stats_ads))
            msg = data.get("message", "")
            self.append_log("TABCHI", f"[ADVERT SENT] '{msg}'")

        elif event_type == "warn":
            t = data.get("text", "")
            self.append_log("WARN", f"[!] {t}")

        elif event_type == "error":
            err = data.get("error", "")
            self.append_log("ERROR", f"[ERROR] {err}")

    # ── Terminal Logger Helper ───────────────────────────────────────────────
    def append_log(self, tag: str, message: str):
        now = time.strftime("%H:%M:%S")
        prefix = f"[{now}] [{tag.upper()}]"
        line = f"{prefix:<20} {message}\n"

        self.txt_log.insert("end", line)
        self.txt_log.see("end")

    def clear_logs(self):
        self.txt_log.delete("1.0", "end")
        self.append_log("INFO", "Logs cleared.")


def launch_gui():
    app = MythoriaGUI()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
