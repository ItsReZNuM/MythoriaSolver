"""
Solvers & Game Delays Tab
Configure individual solver heuristics, response delays, and self-learning filters.
"""
import tkinter as tk
from typing import Dict, Any
import customtkinter as ctk

from settings import (
    Settings,
    GAME_TYPES,
    GAME_TYPE_LABELS,
    GameTypeDelay,
)
from ui.theme import (
    get_font,
    C_BG,
    C_BORDER,
    C_SUCCESS,
)
from ui.components import (
    SmoothScrollableFrame,
    create_settings_section,
    add_entry_row,
    add_switch_row,
)


class SolversTab(SmoothScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=C_BG)
        self.grid_columnconfigure(0, weight=1)

        # ── Global Fallback Delays ──
        s_glob = create_settings_section(
            self, "GLOBAL FALLBACK DELAYS",
            "Used when a game type does not have specific delay overrides"
        )
        self.ent_glob_min = add_entry_row(s_glob, "Global Min Delay (Seconds)", "Minimum human wait time before submitting")
        self.ent_glob_max = add_entry_row(s_glob, "Global Max Delay (Seconds)", "Maximum human wait time before submitting")

        # ── 7 Solvers Configuration ──
        s_solvers = create_settings_section(
            self, "SOLVER ENGINES & PER-TYPE DELAYS",
            "Enable/disable specific solvers and configure customized response delays"
        )

        self.solver_widgets: Dict[str, Dict[str, Any]] = {}

        for gt in GAME_TYPES:
            card = ctk.CTkFrame(s_solvers, fg_color="#12151d", corner_radius=6, border_width=1, border_color=C_BORDER)
            card.pack(fill="x", padx=14, pady=6)
            card.grid_columnconfigure(1, weight=1)

            sw = ctk.CTkSwitch(
                card, text=f"  {GAME_TYPE_LABELS.get(gt, gt)}",
                font=get_font(12, "bold"), progress_color=C_SUCCESS
            )
            sw.grid(row=0, column=0, padx=12, pady=10, sticky="w")

            delays_frame = tk.Frame(card, bg="#12151d")
            delays_frame.grid(row=0, column=1, padx=12, pady=6, sticky="e")

            ctk.CTkLabel(delays_frame, text="Min (s):", font=get_font(11), fg_color="#12151d").pack(side="left", padx=4)
            ent_min = ctk.CTkEntry(delays_frame, width=64, height=28, font=get_font(11))
            ent_min.pack(side="left", padx=(0, 10))

            ctk.CTkLabel(delays_frame, text="Max (s):", font=get_font(11), fg_color="#12151d").pack(side="left", padx=4)
            ent_max = ctk.CTkEntry(delays_frame, width=64, height=28, font=get_font(11))
            ent_max.pack(side="left")

            self.solver_widgets[gt] = {
                "switch": sw,
                "min": ent_min,
                "max": ent_max,
            }

        # ── Self-Learning Engine ──
        s_learn = create_settings_section(
            self, "AUTO-LEARNING ENGINE",
            "Automatically learn new Minecraft words and trivia answers announced in chat"
        )
        self.sw_auto_learn = add_switch_row(s_learn, "Auto-Learn New Words from Game Winner Announcements")
        self.ent_learn_min_len = add_entry_row(s_learn, "Min Word Length", "Ignore answers shorter than this length (default: 3)")
        self.sw_filter_random = add_switch_row(s_learn, "Filter Random String Noise (Prevents memorizing anti-bot gibberish like 'zK9xP')")

    def populate(self, settings: Settings):
        self.ent_glob_min.delete(0, "end")
        self.ent_glob_min.insert(0, str(settings.global_min_delay))
        self.ent_glob_max.delete(0, "end")
        self.ent_glob_max.insert(0, str(settings.global_max_delay))

        for gt, widgets in self.solver_widgets.items():
            gd = settings.game_delays.get(gt, GameTypeDelay())
            if gd.enabled:
                widgets["switch"].select()
            else:
                widgets["switch"].deselect()

            widgets["min"].delete(0, "end")
            widgets["min"].insert(0, str(gd.min_delay))

            widgets["max"].delete(0, "end")
            widgets["max"].insert(0, str(gd.max_delay))

        if settings.auto_learn_words:
            self.sw_auto_learn.select()
        else:
            self.sw_auto_learn.deselect()

        self.ent_learn_min_len.delete(0, "end")
        self.ent_learn_min_len.insert(0, str(settings.auto_learn_min_length))

        if settings.auto_learn_filter_random:
            self.sw_filter_random.select()
        else:
            self.sw_filter_random.deselect()

    def apply(self, settings: Settings):
        try:
            settings.global_min_delay = float(self.ent_glob_min.get())
            settings.global_max_delay = float(self.ent_glob_max.get())
        except ValueError:
            settings.global_min_delay = 3.0
            settings.global_max_delay = 7.0

        for gt, widgets in self.solver_widgets.items():
            en = bool(widgets["switch"].get())
            try:
                mn = float(widgets["min"].get())
                mx = float(widgets["max"].get())
            except ValueError:
                mn, mx = 3.0, 7.0
            settings.game_delays[gt] = GameTypeDelay(min_delay=mn, max_delay=mx, enabled=en)

        settings.auto_learn_words = bool(self.sw_auto_learn.get())
        try:
            settings.auto_learn_min_length = int(self.ent_learn_min_len.get())
        except ValueError:
            settings.auto_learn_min_length = 3
        settings.auto_learn_filter_random = bool(self.sw_filter_random.get())
