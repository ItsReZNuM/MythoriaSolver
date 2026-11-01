"""
General & Minecraft Configuration Tab
Player account identity, Minecraft log selector, typing methods, and delays.
"""
from typing import Callable, Optional
import customtkinter as ctk

from settings import Settings
from ui.theme import (
    get_font,
    C_BORDER,
    C_ACCENT,
    C_ACCENT_HOVER,
    C_TEXT,
)
from ui.components import (
    create_settings_section,
    add_entry_row,
    add_switch_row,
)


class GeneralTab(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        get_icon: Callable[[str], Optional[ctk.CTkImage]],
        on_browse_log: Callable[[], None],
        on_detect_log: Callable[[], None],
    ):
        super().__init__(master, fg_color="transparent")
        self.get_icon = get_icon
        self.on_browse_log = on_browse_log
        self.on_detect_log = on_detect_log

        self.grid_columnconfigure(0, weight=1)

        # ── Section 1: Player Identity ──
        s1 = create_settings_section(
            self, "PLAYER IDENTITY",
            "Minecraft in-game identity for winner detection and chat targeting"
        )
        self.ent_username = add_entry_row(s1, "Minecraft Username", "Exact in-game display name (case-sensitive)")

        # ── Section 2: Log File & Launcher ──
        s2 = create_settings_section(
            self, "MINECRAFT INSTALLATION & LOG FILE",
            "Specify or auto-detect active latest.log path across all Minecraft launchers"
        )
        path_row = ctk.CTkFrame(s2, fg_color="transparent")
        path_row.pack(fill="x", padx=14, pady=6)
        lbl_p = ctk.CTkLabel(path_row, text="Active latest.log Path", font=get_font(11, "bold"), text_color=C_TEXT)
        lbl_p.pack(anchor="w")

        path_input_row = ctk.CTkFrame(path_row, fg_color="transparent")
        path_input_row.pack(fill="x", pady=(4, 0))
        path_input_row.grid_columnconfigure(0, weight=1)

        self.ent_log_path = ctk.CTkEntry(
            path_input_row, font=get_font(11), fg_color="#12151d",
            border_color=C_BORDER, height=34
        )
        self.ent_log_path.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        btn_browse = ctk.CTkButton(
            path_input_row, text="Browse", image=self.get_icon("folder"), compound="left",
            font=get_font(11, "bold"), fg_color="#334155", hover_color="#475569",
            width=90, height=34, command=self.on_browse_log
        )
        btn_browse.grid(row=0, column=1, padx=(0, 8))

        btn_detect = ctk.CTkButton(
            path_input_row, text="Auto-Detect", image=self.get_icon("refresh"), compound="left",
            font=get_font(11, "bold"), fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
            text_color="#0f172a", width=120, height=34, command=self.on_detect_log
        )
        btn_detect.grid(row=0, column=2)

        # ── Section 3: Keyboard & Interaction ──
        s3 = create_settings_section(
            self, "AUTOMATION & INPUT SIMULATION",
            "Control keyboard scan codes, focus verification, and typing behavior"
        )
        self.sw_dry_run = add_switch_row(s3, "Dry-Run Mode (Simulation only, no physical keystrokes sent)")
        self.sw_require_focus = add_switch_row(s3, "Require Minecraft Window Focus (Prevents typing while alt-tabbed)")

        send_m_row = ctk.CTkFrame(s3, fg_color="transparent")
        send_m_row.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(send_m_row, text="Send Method", font=get_font(11, "bold")).pack(side="left")
        self.seg_send_method = ctk.CTkSegmentedButton(
            send_m_row, values=["paste", "write"],
            font=get_font(11, "bold"), selected_color=C_ACCENT, selected_hover_color=C_ACCENT_HOVER,
            command=self._update_send_method_desc
        )
        self.seg_send_method.pack(side="right")

        self.lbl_send_method_desc = ctk.CTkLabel(
            s3, text="", font=get_font(10), text_color="#38bdf8", justify="left", anchor="w"
        )
        self.lbl_send_method_desc.pack(fill="x", padx=14, pady=(0, 6))

        self.ent_chat_key = add_entry_row(s3, "Chat Key", "Key used to open chat in Minecraft (default: 't')")
        self.ent_cooldown = add_entry_row(s3, "Server Cooldown (Seconds)", "Minimum delay between consecutive chat messages (server limit: 3.0s)")
        self.ent_open_delay = add_entry_row(s3, "Post Open Chat Delay (Seconds)", "Wait time between pressing chat key and typing answer (default: 0.25)")
        self.ent_type_delay = add_entry_row(s3, "Post Type Delay (Seconds)", "Wait time between typing answer and pressing Enter (default: 0.10)")
        self.ent_retries = add_entry_row(s3, "Max Candidate Retries", "How many backup candidates to attempt if first answer isn't accepted (default: 2)")

        # ── Section 4: Answering Policies ──
        s4 = create_settings_section(
            self, "ANSWERING FREQUENCY & NUMBER STRATEGY",
            "Configure ratio of games answered and number guessing modes"
        )
        self.ent_ratio = add_entry_row(s4, "Answer Ratio", "Answer 1 of every N games (1 = answer 100%, 2 = answer 50%, 3 = answer 33%)")

        guess_m_row = ctk.CTkFrame(s4, fg_color="transparent")
        guess_m_row.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(guess_m_row, text="Guess Number Strategy", font=get_font(11, "bold")).pack(side="left")
        self.seg_guess_mode = ctk.CTkSegmentedButton(
            guess_m_row, values=["all", "binary_search", "random", "single", "skip"],
            font=get_font(11, "bold"), selected_color=C_ACCENT, selected_hover_color=C_ACCENT_HOVER,
            command=self._update_guess_mode_desc
        )
        self.seg_guess_mode.pack(side="right")

        self.lbl_guess_desc = ctk.CTkLabel(
            s4, text="", font=get_font(10), text_color="#38bdf8", justify="left", anchor="w"
        )
        self.lbl_guess_desc.pack(fill="x", padx=14, pady=(0, 6))

    def _update_send_method_desc(self, value=None):
        val = value or self.seg_send_method.get()
        descs = {
            "paste": "📋 paste: ارسال با چسباندن کلیپ‌بورد (Ctrl+V) — سریع‌ترین متد و کاملاً مستقل از زبان کیبورد ویندوز (فارسی/انگلیسی)",
            "write": "⌨️ write: تایپ شبیه‌سازی‌شده کاراکتر به کاراکتر با وقفه میلی‌ثانیه‌ای مشابه تایپ واقعی انسان",
        }
        self.lbl_send_method_desc.configure(text=descs.get(val, ""))

    def _update_guess_mode_desc(self, value=None):
        val = value or self.seg_guess_mode.get()
        descs = {
            "all": "🔢 all (تمام اعداد): تمام اعداد بازه را به نوبت در هر کول‌داون ۳ ثانیه‌ای امتحان می‌کند تا برنده شود.",
            "binary_search": "🎯 binary_search (جستجوی دودویی): عدد میانی بازه را حدس می‌زند تا سریع‌ترین راه برای یافتن عدد باشد.",
            "random": "🎲 random (حدس تصادفی): در هر نوبت یک عدد تصادفی از اعداد باقی‌مانده بازه را حدس می‌زند.",
            "single": "☝️ single (تک حدس): فقط یک حدس در شروع بازی ارسال می‌کند و پیام دیگری نمی‌فرستد.",
            "skip": "🚫 skip (صرف‌نظر): بازی‌های حدس عدد را کاملاً نادیده می‌گیرد و هیچ عددی ارسال نمی‌کند.",
        }
        self.lbl_guess_desc.configure(text=descs.get(val, ""))

    def populate(self, settings: Settings):
        self.ent_username.delete(0, "end")
        self.ent_username.insert(0, settings.player_username)

        self.ent_log_path.delete(0, "end")
        self.ent_log_path.insert(0, settings.minecraft_log_path)

        if settings.dry_run:
            self.sw_dry_run.select()
        else:
            self.sw_dry_run.deselect()

        if settings.require_focus:
            self.sw_require_focus.select()
        else:
            self.sw_require_focus.deselect()

        self.seg_send_method.set(settings.send_method)
        self._update_send_method_desc(settings.send_method)

        self.ent_chat_key.delete(0, "end")
        self.ent_chat_key.insert(0, settings.chat_key)

        self.ent_cooldown.delete(0, "end")
        self.ent_cooldown.insert(0, str(settings.send_cooldown))

        self.ent_open_delay.delete(0, "end")
        self.ent_open_delay.insert(0, str(getattr(settings, "post_open_chat_delay", 0.25)))

        self.ent_type_delay.delete(0, "end")
        self.ent_type_delay.insert(0, str(getattr(settings, "post_type_delay", 0.10)))

        self.ent_retries.delete(0, "end")
        self.ent_retries.insert(0, str(settings.max_candidate_retries))

        self.ent_ratio.delete(0, "end")
        self.ent_ratio.insert(0, str(settings.answer_ratio))

        self.seg_guess_mode.set(settings.guess_number_mode)
        self._update_guess_mode_desc(settings.guess_number_mode)

    def apply(self, settings: Settings):
        settings.player_username = self.ent_username.get().strip() or "Player"
        settings.minecraft_log_path = self.ent_log_path.get().strip()
        settings.dry_run = bool(self.sw_dry_run.get())
        settings.require_focus = bool(self.sw_require_focus.get())
        settings.send_method = self.seg_send_method.get()
        settings.chat_key = self.ent_chat_key.get().strip() or "t"

        try:
            settings.send_cooldown = float(self.ent_cooldown.get())
        except ValueError:
            settings.send_cooldown = 3.0

        try:
            settings.post_open_chat_delay = float(self.ent_open_delay.get())
        except ValueError:
            settings.post_open_chat_delay = 0.25

        try:
            settings.post_type_delay = float(self.ent_type_delay.get())
        except ValueError:
            settings.post_type_delay = 0.10

        try:
            settings.max_candidate_retries = int(self.ent_retries.get())
        except ValueError:
            settings.max_candidate_retries = 2

        try:
            settings.answer_ratio = max(1, int(self.ent_ratio.get()))
        except ValueError:
            settings.answer_ratio = 1

        settings.guess_number_mode = self.seg_guess_mode.get()
