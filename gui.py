"""
MythoriaSolver - Modern CustomTkinter Graphical User Interface
Modular Architecture:
  - ui/theme.py: Deep Obsidian Dark Theme & JetBrains Mono typography
  - ui/components.py: Reusable cards, styled inputs, and toggle switches
  - ui/tabs/: Dedicated modules for each functional area:
      1. DashboardTab: Live chat monitoring, answer dispatch & live telemetry
      2. GeneralTab: Player account identity, Minecraft log selector, typing methods, delays
      3. SolversTab: Solver heuristics, individual delays, auto-learning
      4. StealthTab: Human typo simulation, fake mistakes, anti-cheat evasion
      5. TabchiTab: Automated auction promotion, interval scheduling, dot duplicate bypass
      6. SandboxTab: Interactive puzzle solver playground & historical analytics
"""
import sys
import os
import queue
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List

import customtkinter as ctk
from tkinter import filedialog, messagebox

from config import config
from settings import (
    Settings,
    SETTINGS_FILE,
)
from minecraft.log_finder import detect_minecraft_logs
from solver.router import SolverRouter
from database.models import DatabaseManager

# UI Theme & Modular Tab Components
from ui.theme import (
    FONT_NAME,
    get_font,
    load_icons,
    C_BG,
    C_SIDEBAR,
    C_CARD,
    C_CARD_HOVER,
    C_BORDER,
    C_ACCENT,
    C_ACCENT_HOVER,
    C_SUCCESS,
    C_DANGER,
    C_WARNING,
    C_TEXT,
    C_TEXT_MUTED,
)
from ui.tabs import (
    DashboardTab,
    GeneralTab,
    SolversTab,
    StealthTab,
    TabchiTab,
    SandboxTab,
)

# Appearance Configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


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
        self.icons = load_icons()

        self.configure(fg_color=C_BG)

        # Build Main UI Layout & Modular Tabs
        self._create_layout()

        # Load settings into all UI controls
        self._populate_all_settings()

        # Start Event Queue Poller
        self.after(50, self._process_event_queue)

        # Force off-screen layout completion and smoothly reveal window
        self.update()
        self.deiconify()

    def get_icon(self, name: str) -> Optional[ctk.CTkImage]:
        return self.icons.get(name)

    # ── Layout Construction ──────────────────────────────────────────────────
    def _create_layout(self):
        # 2-Column Grid: Sidebar (Col 0) and Main Content (Col 1)
        self.grid_columnconfigure(0, weight=0, minsize=220)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──
        self.sidebar = ctk.CTkFrame(self, fg_color=C_SIDEBAR, corner_radius=0, width=220)
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
            font=get_font(16, "bold"), text_color=C_TEXT
        )
        lbl_brand.pack(anchor="w")
        lbl_sub = ctk.CTkLabel(
            title_box, text="SMP Chat Solver",
            font=get_font(10), text_color=C_ACCENT
        )
        lbl_sub.pack(anchor="w")

        # Separator
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=C_BORDER)
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
                text_color=C_TEXT_MUTED,
                hover_color=C_CARD_HOVER,
                command=lambda tid=tab_id: self.switch_tab(tid),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self.nav_buttons[tab_id] = btn

        # Sidebar Footer: Bot Control Card
        sidebar_bottom = ctk.CTkFrame(self.sidebar, fg_color=C_CARD, corner_radius=10)
        sidebar_bottom.pack(side="bottom", fill="x", padx=12, pady=16)

        # Status Pill
        self.status_pill = ctk.CTkLabel(
            sidebar_bottom,
            text="● STOPPED",
            font=get_font(11, "bold"),
            text_color=C_DANGER,
        )
        self.status_pill.pack(pady=(10, 6))

        # Master Start / Stop Button
        self.btn_master_toggle = ctk.CTkButton(
            sidebar_bottom,
            text=" START BOT",
            image=self.get_icon("play"),
            compound="left",
            font=get_font(12, "bold"),
            fg_color=C_SUCCESS,
            hover_color="#16a34a",
            height=36,
            corner_radius=6,
            command=self.toggle_bot,
        )
        self.btn_master_toggle.pack(fill="x", padx=10, pady=(0, 10))

        # ── Main Content Area ──
        self.main_content = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
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

        # Instantiate all modular tab views
        self.tab_dashboard = DashboardTab(self.tab_container, self.get_icon, self.start_bot, self.stop_bot)
        self.tab_general = GeneralTab(self.tab_container, self.get_icon, self._browse_log_file, self._open_instance_selector)
        self.tab_solvers = SolversTab(self.tab_container)
        self.tab_stealth = StealthTab(self.tab_container)
        self.tab_tabchi = TabchiTab(self.tab_container, self.get_icon)
        self.tab_sandbox = SandboxTab(self.tab_container, self.router, self.db, self.get_icon)

        self.tab_frames = {
            "dashboard": self.tab_dashboard,
            "general": self.tab_general,
            "solvers": self.tab_solvers,
            "stealth": self.tab_stealth,
            "tabchi": self.tab_tabchi,
            "sandbox": self.tab_sandbox,
        }

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
            font=get_font(20, "bold"), text_color=C_TEXT
        )
        self.lbl_page_title.pack(anchor="w")

        self.lbl_page_desc = ctk.CTkLabel(
            title_frame, text="Real-time chat game monitoring, answer dispatch & live telemetry",
            font=get_font(11), text_color=C_TEXT_MUTED
        )
        self.lbl_page_desc.pack(anchor="w")

        actions_frame = ctk.CTkFrame(header, fg_color="transparent")
        actions_frame.grid(row=0, column=1, sticky="e")

        self.lbl_save_status = ctk.CTkLabel(
            actions_frame, text="",
            font=get_font(11, "bold"), text_color=C_SUCCESS
        )
        self.lbl_save_status.pack(side="left", padx=(0, 10))

        btn_save = ctk.CTkButton(
            actions_frame,
            text=" SAVE SETTINGS",
            image=self.get_icon("save"),
            compound="left",
            font=get_font(12, "bold"),
            fg_color=C_ACCENT,
            hover_color=C_ACCENT_HOVER,
            text_color="#0f172a",
            height=36,
            corner_radius=6,
            command=self.save_all_settings,
        )
        btn_save.pack(side="left")

    # ── Tab Navigation (Instant Switch) ──────────────────────────────────────
    def switch_tab(self, tab_id: str):
        self.current_tab = tab_id

        # Update button highlights & icons
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.configure(
                    fg_color=C_CARD,
                    text_color=C_ACCENT,
                    image=self.get_icon(f"{tid}_active") or self.get_icon(tid)
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=C_TEXT_MUTED,
                    image=self.get_icon(tid)
                )

        # Instant 0ms visual switch: map target frame and unmap others cleanly
        for tid, frame in self.tab_frames.items():
            if tid == tab_id:
                frame.grid()
                actual_widget = getattr(frame, "_parent_frame", frame)
                actual_widget.tkraise()
            else:
                frame.grid_remove()

        # Synchronize layout instantly to prevent frame-by-frame pop-in
        self.update_idletasks()

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

    # ── Populate Settings into UI ────────────────────────────────────────────
    def _populate_all_settings(self):
        self.tab_general.populate(self.settings)
        self.tab_solvers.populate(self.settings)
        self.tab_stealth.populate(self.settings)
        self.tab_tabchi.populate(self.settings)
        self._update_telemetry()

    def _update_telemetry(self):
        active_p = self.settings.get_active_log_path()
        self.tab_dashboard.update_telemetry(
            player=self.settings.player_username,
            log_name=active_p.name,
            config_path="%APPDATA%/MythoriaSolver/settings.json"
        )

    def save_all_settings(self):
        """Save settings to %APPDATA%/MythoriaSolver/settings.json and provide UI feedback."""
        self.tab_general.apply(self.settings)
        self.tab_solvers.apply(self.settings)
        self.tab_stealth.apply(self.settings)
        self.tab_tabchi.apply(self.settings)
        self.settings.save()

        self._update_telemetry()
        self.lbl_save_status.configure(text="Settings Saved ✓")
        self.append_log("INFO", f"Settings saved to {SETTINGS_FILE}")
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
            self.tab_general.ent_log_path.delete(0, "end")
            self.tab_general.ent_log_path.insert(0, path)

    def _open_instance_selector(self):
        """Discovers all installed Minecraft launchers and lets user pick with 1 click."""
        instances = detect_minecraft_logs(custom_path=self.tab_general.ent_log_path.get())
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
            font=get_font(14, "bold"), text_color=C_TEXT
        )
        lbl.pack(padx=16, pady=(16, 8), anchor="w")

        sub = ctk.CTkLabel(
            top, text="Sorted by most recently modified logs. Click 'Select' to use.",
            font=get_font(11), text_color=C_TEXT_MUTED
        )
        sub.pack(padx=16, pady=(0, 10), anchor="w")

        sf = ctk.CTkScrollableFrame(top, fg_color="#12151d", border_width=1, border_color=C_BORDER)
        sf.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        sf.grid_columnconfigure(0, weight=1)

        for inst in instances:
            row = ctk.CTkFrame(sf, fg_color=C_CARD, corner_radius=6)
            row.pack(fill="x", pady=4, padx=4)
            row.grid_columnconfigure(0, weight=1)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.grid(row=0, column=0, sticky="w", padx=10, pady=8)

            name_lbl = ctk.CTkLabel(info, text=inst.name, font=get_font(12, "bold"), text_color=C_ACCENT)
            name_lbl.pack(anchor="w")

            detail_lbl = ctk.CTkLabel(
                info, text=f"Last modified: {inst.formatted_mtime} | {inst.path}",
                font=get_font(10), text_color=C_TEXT_MUTED
            )
            detail_lbl.pack(anchor="w")

            def choose_instance(p=inst.path):
                self.tab_general.ent_log_path.delete(0, "end")
                self.tab_general.ent_log_path.insert(0, str(p.resolve()))
                top.destroy()
                self.save_all_settings()

            btn = ctk.CTkButton(
                row, text="Select", width=70, height=28,
                font=get_font(11, "bold"), fg_color=C_SUCCESS, hover_color="#16a34a",
                command=choose_instance
            )
            btn.grid(row=0, column=1, padx=10, pady=8)

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

        replay_active = bool(self.tab_dashboard.sw_replay.get())

        self.is_running = True
        self.status_pill.configure(text="● RUNNING", text_color=C_SUCCESS)
        self.btn_master_toggle.configure(text=" STOP BOT", fg_color=C_DANGER, hover_color="#dc2626", image=self.get_icon("stop"))

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
        self.status_pill.configure(text="● STOPPED", text_color=C_DANGER)
        self.btn_master_toggle.configure(text=" START BOT", fg_color=C_SUCCESS, hover_color="#16a34a", image=self.get_icon("play"))

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
            self.status_pill.configure(text="● STOPPED", text_color=C_DANGER)
            self.btn_master_toggle.configure(text=" START BOT", fg_color=C_SUCCESS, hover_color="#16a34a", image=self.get_icon("play"))

        elif event_type == "question":
            self.stats_games += 1
            self.tab_dashboard.set_stat_games(self.stats_games)

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
                self.append_log("LOST", f"✗ Game Lost. Winner: {winner} | Answer: '{ans}'{dur_str}")

            win_pct = (self.stats_wins / self.stats_games * 100) if self.stats_games > 0 else 0
            self.tab_dashboard.set_stat_wins(self.stats_wins, win_pct)

        elif event_type == "learned_word":
            w = data.get("word", "")
            self.append_log("LEARN", f"  + Learned new word added to DB: '{w}'")

        elif event_type == "learned_trivia":
            q = data.get("question", "")
            a = data.get("answer", "")
            self.append_log("LEARN", f"  + Learned trivia Q&A: '{q}' -> '{a}'")

        elif event_type == "advert_sent":
            self.stats_ads += 1
            self.tab_dashboard.set_stat_ads(self.stats_ads)
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
        self.tab_dashboard.append_log(tag, message)

    def clear_logs(self):
        self.tab_dashboard.clear_logs()


def launch_gui():
    app = MythoriaGUI()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
