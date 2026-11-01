"""
Dashboard & Live Monitor Tab
Real-time chat game monitoring, answer dispatch & live telemetry.
"""
import time
from typing import Callable, Optional
import customtkinter as ctk

from ui.theme import (
    get_font,
    C_CARD,
    C_BORDER,
    C_ACCENT,
    C_SUCCESS,
    C_DANGER,
    C_WARNING,
    C_TEXT_MUTED,
)
from ui.components import create_stat_card


class DashboardTab(ctk.CTkFrame):
    def __init__(
        self,
        master,
        get_icon: Callable[[str], Optional[ctk.CTkImage]],
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
    ):
        super().__init__(master, fg_color="transparent")
        self.get_icon = get_icon
        self.on_start = on_start
        self.on_stop = on_stop

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Top Stats Cards (4 horizontal) ──
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)

        self.card_games = create_stat_card(stats_frame, 0, "GAMES DETECTED", "0", C_ACCENT)
        self.card_wins = create_stat_card(stats_frame, 1, "GAMES WON", "0 (0%)", C_SUCCESS)
        self.card_accuracy = create_stat_card(stats_frame, 2, "BOT ACCURACY", "0.0%", C_WARNING)
        self.card_ads = create_stat_card(stats_frame, 3, "ADS SENT", "0", "#c084fc")

        # ── Control Bar ──
        ctrl_frame = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=8, height=48)
        ctrl_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        self.btn_start = ctk.CTkButton(
            ctrl_frame, text=" START MONITORING",
            image=self.get_icon("play"), compound="left",
            font=get_font(12, "bold"), fg_color=C_SUCCESS, hover_color="#16a34a",
            height=32, corner_radius=6, command=self.on_start
        )
        self.btn_start.pack(side="left", padx=(12, 6), pady=8)

        self.btn_stop = ctk.CTkButton(
            ctrl_frame, text=" STOP",
            image=self.get_icon("stop"), compound="left",
            font=get_font(12, "bold"), fg_color=C_DANGER, hover_color="#dc2626",
            height=32, corner_radius=6, command=self.on_stop
        )
        self.btn_stop.pack(side="left", padx=6, pady=8)

        self.btn_clear = ctk.CTkButton(
            ctrl_frame, text=" CLEAR LOGS",
            image=self.get_icon("trash"), compound="left",
            font=get_font(11, "bold"), fg_color="#334155", hover_color="#475569",
            height=32, corner_radius=6, command=self.clear_logs
        )
        self.btn_clear.pack(side="left", padx=6, pady=8)

        self.sw_replay = ctk.CTkSwitch(
            ctrl_frame, text="Replay Historical Log",
            font=get_font(11), progress_color=C_ACCENT
        )
        self.sw_replay.pack(side="right", padx=14, pady=8)

        # ── Terminal / Live Feed Textbox ──
        self.txt_log = ctk.CTkTextbox(
            self,
            fg_color="#0a0c10",
            text_color="#e2e8f0",
            font=get_font(11),
            corner_radius=8,
            border_width=1,
            border_color=C_BORDER,
            wrap="word",
        )
        self.txt_log.grid(row=2, column=0, sticky="nsew", pady=(0, 8))

        # Color Tags for Live Visual Terminal Feed
        self.txt_log.tag_config("WINNER", foreground="#22c55e")     # Vibrant Emerald Green (Our Bot Won!)
        self.txt_log.tag_config("LOST", foreground="#f87171")       # Coral Rose/Red (Game Lost / Timeout)
        self.txt_log.tag_config("ANSWER", foreground="#38bdf8")     # Electric Cyan (Answers Sent by Bot)
        self.txt_log.tag_config("QUESTION", foreground="#facc15")   # Radiant Amber / Yellow (Game Questions)
        self.txt_log.tag_config("SOLVER", foreground="#38bdf8")     # Sky Blue (Candidate Results)
        self.txt_log.tag_config("GAME", foreground="#c084fc")       # Purple (Game Header)
        self.txt_log.tag_config("STEALTH", foreground="#e879f9")    # Magenta (Fake Typo Injected)
        self.txt_log.tag_config("TABCHI", foreground="#60a5fa")     # Blue (Promotional Ad Dispatched)
        self.txt_log.tag_config("LEARN", foreground="#34d399")      # Mint Green (Self-Learning Q&A / Word)
        self.txt_log.tag_config("WARN", foreground="#fb923c")       # Orange (Skipped / Filtered)
        self.txt_log.tag_config("ERROR", foreground="#ef4444")      # Crimson Red (Runtime Errors)
        self.txt_log.tag_config("INFO", foreground="#94a3b8")       # Slate Muted Gray (General Info)
        self.txt_log.tag_config("TIMESTAMP", foreground="#64748b")  # Dark Slate (Timestamps)

        # ── Bottom Telemetry Bar ──
        self.telemetry_strip = ctk.CTkLabel(
            self,
            text="Active Player: Initializing... | Config: %APPDATA%/MythoriaSolver",
            font=get_font(10), text_color=C_TEXT_MUTED, anchor="w"
        )
        self.telemetry_strip.grid(row=3, column=0, sticky="ew")

        # Initial Welcome Log Line
        self.append_log("INFO", "MythoriaSolver GUI initialized and ready.")

    def append_log(self, tag: str, message: str):
        """Appends formatted, syntax-highlighted timestamped log line to the live terminal view."""
        now = time.strftime("%H:%M:%S")
        tag_upper = tag.upper()

        # Insert muted timestamp prefix
        self.txt_log.insert("end", f"[{now}] ", "TIMESTAMP")
        # Insert color-coded tag badge
        self.txt_log.insert("end", f"[{tag_upper:<8}] ", tag_upper)
        # Insert message body with matching tag highlight
        self.txt_log.insert("end", f"{message}\n", tag_upper)
        self.txt_log.see("end")

    def clear_logs(self):
        """Clears the live terminal view."""
        self.txt_log.delete("1.0", "end")
        self.append_log("INFO", "Logs cleared.")

    def update_telemetry(self, player: str, log_name: str, config_path: str):
        self.telemetry_strip.configure(
            text=f"Active Player: {player} | Log: {log_name} | Config: {config_path}"
        )

    def set_stat_games(self, count: int):
        self.card_games.configure(text=str(count))

    def set_stat_wins(self, wins: int, win_pct: float):
        self.card_wins.configure(text=f"{wins} ({win_pct:.0f}%)")

    def set_stat_accuracy(self, acc_pct: float):
        self.card_accuracy.configure(text=f"{acc_pct:.1f}%")

    def set_stat_ads(self, count: int):
        self.card_ads.configure(text=str(count))
