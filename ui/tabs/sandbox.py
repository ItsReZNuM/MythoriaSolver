"""
Interactive Sandbox & Statistics Tab
Direct puzzle solver testing playground and historical win rate analytics.
"""
import time
from typing import Callable, Optional
import customtkinter as ctk

from config import config
from settings import (
    GAME_TYPES,
    GAME_TYPE_LABELS,
    SETTINGS_FILE,
)
from solver.router import SolverRouter
from database.models import DatabaseManager
from ui.theme import (
    get_font,
    C_BORDER,
    C_ACCENT,
    C_ACCENT_HOVER,
    C_SUCCESS,
    C_DANGER,
    C_TEXT,
    C_TEXT_MUTED,
)
from ui.components import create_settings_section


class SandboxTab(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        router: SolverRouter,
        db: DatabaseManager,
        get_icon: Callable[[str], Optional[ctk.CTkImage]],
    ):
        super().__init__(master, fg_color="transparent")
        self.router = router
        self.db = db
        self.get_icon = get_icon

        self.grid_columnconfigure(0, weight=1)

        # ── Solver Sandbox ──
        s_box = create_settings_section(
            self, "INSTANT SOLVER SANDBOX",
            "Test any chat game puzzle or math expression with live solver verification"
        )

        test_row = ctk.CTkFrame(s_box, fg_color="transparent")
        test_row.pack(fill="x", padx=14, pady=8)
        test_row.grid_columnconfigure(0, weight=1)

        self.ent_sandbox_input = ctk.CTkEntry(
            test_row, placeholder_text="e.g. 'c_w' or 'e e p r e c r' or '24 * (5 + 3)' or '1-50'...",
            font=get_font(12), height=38, fg_color="#12151d", border_color=C_BORDER
        )
        self.ent_sandbox_input.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.ent_sandbox_input.bind("<Return>", lambda e: self.test_solve())

        self.opt_sandbox_type = ctk.CTkOptionMenu(
            test_row,
            values=["Auto-Detect"] + [GAME_TYPE_LABELS.get(gt, gt) for gt in GAME_TYPES],
            font=get_font(11, "bold"), fg_color="#334155", button_color="#475569",
            height=38, width=170
        )
        self.opt_sandbox_type.grid(row=0, column=1, padx=(0, 8))

        btn_solve = ctk.CTkButton(
            test_row, text=" SOLVE", image=self.get_icon("bolt"), compound="left",
            font=get_font(12, "bold"), fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
            text_color="#0f172a", height=38, width=100, command=self.test_solve
        )
        btn_solve.grid(row=0, column=2)

        # Sandbox Result Card
        self.sandbox_result_card = ctk.CTkFrame(s_box, fg_color="#12151d", corner_radius=6, border_width=1, border_color=C_BORDER)
        self.sandbox_result_card.pack(fill="x", padx=14, pady=(0, 10))

        self.lbl_sandbox_output = ctk.CTkLabel(
            self.sandbox_result_card, text="Enter a puzzle question above and click Solve.",
            font=get_font(11), text_color=C_TEXT_MUTED, justify="left", anchor="w"
        )
        self.lbl_sandbox_output.pack(fill="x", padx=14, pady=12)

        # ── Database & Historical Analytics ──
        s_db = create_settings_section(
            self, "DATABASE & HISTORICAL PERFORMANCE",
            "Local database item count and persistent session statistics"
        )

        db_info_frame = ctk.CTkFrame(s_db, fg_color="transparent")
        db_info_frame.pack(fill="x", padx=14, pady=8)

        total_db_items = len(self.db.all_items)
        lbl_db_items = ctk.CTkLabel(
            db_info_frame, text=f"• Verified Database Items: {total_db_items:,} Minecraft blocks/items/mobs",
            font=get_font(12, "bold"), text_color=C_TEXT
        )
        lbl_db_items.pack(anchor="w", pady=2)

        settings_path_lbl = ctk.CTkLabel(
            db_info_frame, text=f"• Persistent Settings Path: {SETTINGS_FILE}",
            font=get_font(11), text_color=C_ACCENT
        )
        settings_path_lbl.pack(anchor="w", pady=2)

        db_path_lbl = ctk.CTkLabel(
            db_info_frame, text=f"• Database Path: {config.DB_PATH}",
            font=get_font(11), text_color=C_TEXT_MUTED
        )
        db_path_lbl.pack(anchor="w", pady=2)

        # Historical Collector Stats
        self.stats_box = ctk.CTkFrame(s_db, fg_color="#12151d", corner_radius=6, border_width=1, border_color=C_BORDER)
        self.stats_box.pack(fill="x", padx=14, pady=(6, 12))

        self.lbl_hist_stats = ctk.CTkLabel(
            self.stats_box, text="", font=get_font(11, "bold"), text_color=C_SUCCESS
        )
        self.lbl_hist_stats.pack(padx=12, pady=10)
        self.refresh_historical_stats()

    def refresh_historical_stats(self):
        from collector.chat_game_collector import ChatGameCollector
        c = ChatGameCollector()
        stats = c.get_stats()
        hist_text = (
            f"All-Time Logged Games: {stats.get('total_games', 0)}  |  "
            f"Bot Won: {stats.get('won_games', 0)} ({stats.get('win_rate_pct', 0.0)}%)  |  "
            f"Correct Answers: {stats.get('correct_answers', 0)} ({stats.get('accuracy_pct', 0.0)}%)"
        )
        self.lbl_hist_stats.configure(text=hist_text)

    def test_solve(self):
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
            self.lbl_sandbox_output.configure(text=res_str, text_color=C_DANGER)
            return

        lines = [
            f"Detected Type: {GAME_TYPE_LABELS.get(detected, detected)}  |  Solve Time: {elapsed_ms:.2f} ms",
            "Top Candidates:",
        ]
        for i, c in enumerate(candidates[:5], 1):
            lines.append(f"  [{i}] {c['answer']}  (Score: {c['score']:.1f} | Solver: {c.get('solver', 'N/A')})")

        self.lbl_sandbox_output.configure(text="\n".join(lines), text_color=C_SUCCESS)
