"""
Tabchi / Auto-Advertiser Tab
Automated auction promotion, interval scheduling, and anti-duplicate dot bypass.
"""
from typing import Callable, Optional
import customtkinter as ctk

from settings import (
    Settings,
    DEFAULT_TABCHI_MESSAGES,
)
from ui.theme import (
    get_font,
    C_CARD,
    C_BORDER,
    C_ACCENT,
    C_ACCENT_HOVER,
    C_SUCCESS,
    C_DANGER,
    C_TEXT,
    C_TEXT_MUTED,
)
from ui.components import (
    create_settings_section,
    add_entry_row,
    add_switch_row,
)


class TabchiTab(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        get_icon: Callable[[str], Optional[ctk.CTkImage]],
    ):
        super().__init__(master, fg_color="transparent")
        self.get_icon = get_icon
        self.current_messages = list(DEFAULT_TABCHI_MESSAGES)

        self.grid_columnconfigure(0, weight=1)

        # ── Activation ──
        s_master = create_settings_section(
            self, "AUTO-ADVERTISER ACTIVATION",
            "Periodically promote your items, auction listings, or custom chat messages"
        )
        self.sw_tabchi_enabled = add_switch_row(s_master, "Enable Tabchi Auto-Advertiser (تبچی)")

        # ── Interval Schedule ──
        s_timing = create_settings_section(
            self, "INTERVAL & TIMING SCHEDULE",
            "Specify delivery frequencies in minutes"
        )
        self.ent_tabchi_min = add_entry_row(s_timing, "Min Interval (Minutes)", "Shortest wait time before sending next advertisement")
        self.ent_tabchi_max = add_entry_row(s_timing, "Max Interval (Minutes)", "Longest wait time before sending next advertisement")
        self.sw_tabchi_random = add_switch_row(s_timing, "Randomize Interval Between Min and Max (Evades spam timers)")

        # ── Dispatch Rules ──
        s_dispatch = create_settings_section(
            self, "DISPATCH RULES & DUPLICATE BYPASS",
            "Order and server anti-spam filter evasion"
        )

        order_row = ctk.CTkFrame(s_dispatch, fg_color="transparent")
        order_row.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(order_row, text="Message Selection Order", font=get_font(11, "bold")).pack(side="left")
        self.seg_tabchi_order = ctk.CTkSegmentedButton(
            order_row, values=["cycle", "random"],
            font=get_font(11, "bold"), selected_color=C_ACCENT, selected_hover_color=C_ACCENT_HOVER
        )
        self.seg_tabchi_order.pack(side="right")

        self.sw_tabchi_dot = add_switch_row(s_dispatch, "Anti-Duplicate Dot Bypass (Sends '.' before advert to evade server duplicate block)")
        self.ent_tabchi_dot_delay = add_entry_row(s_dispatch, "Dot Cooldown Delay (Seconds)", "Wait time between the dot and the actual message")

        # ── Message List Pool ──
        s_msgs = create_settings_section(
            self, "ADVERTISEMENT MESSAGE POOL",
            "Manage the pool of messages rotated by the auto-advertiser"
        )

        # Input to add new message
        add_frame = ctk.CTkFrame(s_msgs, fg_color="transparent")
        add_frame.pack(fill="x", padx=14, pady=(6, 10))
        add_frame.grid_columnconfigure(0, weight=1)

        self.ent_new_ad = ctk.CTkEntry(
            add_frame, placeholder_text="Enter new advertisement message (/ah view ...)...",
            font=get_font(11), height=34, fg_color="#12151d", border_color=C_BORDER
        )
        self.ent_new_ad.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.ent_new_ad.bind("<Return>", lambda e: self._add_advert_message())

        btn_add_ad = ctk.CTkButton(
            add_frame, text="Add", image=self.get_icon("plus"), compound="left",
            font=get_font(11, "bold"), fg_color=C_SUCCESS, hover_color="#16a34a",
            width=80, height=34, command=self._add_advert_message
        )
        btn_add_ad.grid(row=0, column=1)

        # Messages listbox container
        self.ad_list_frame = ctk.CTkScrollableFrame(
            s_msgs, fg_color="#12151d", height=180, corner_radius=6,
            border_width=1, border_color=C_BORDER
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

        self.lbl_ad_count = ctk.CTkLabel(list_toolbar, text="", font=get_font(11), text_color=C_TEXT_MUTED)
        self.lbl_ad_count.pack(side="right")

    def _refresh_advert_list_ui(self):
        for widget in self.ad_list_frame.winfo_children():
            widget.destroy()

        self.lbl_ad_count.configure(text=f"Total: {len(self.current_messages)} messages")

        if not self.current_messages:
            lbl = ctk.CTkLabel(self.ad_list_frame, text="No advertisements configured.", font=get_font(11), text_color=C_TEXT_MUTED)
            lbl.pack(padx=10, pady=10)
            return

        for idx, msg in enumerate(self.current_messages):
            item = ctk.CTkFrame(self.ad_list_frame, fg_color=C_CARD, corner_radius=4)
            item.pack(fill="x", pady=2, padx=4)
            item.grid_columnconfigure(1, weight=1)

            num_lbl = ctk.CTkLabel(item, text=f"#{idx+1}", font=get_font(10, "bold"), text_color=C_ACCENT, width=32)
            num_lbl.grid(row=0, column=0, padx=(8, 4), pady=4)

            text_lbl = ctk.CTkLabel(item, text=msg, font=get_font(11), text_color=C_TEXT, anchor="w")
            text_lbl.grid(row=0, column=1, sticky="w", padx=4, pady=4)

            def del_msg(i=idx):
                if 0 <= i < len(self.current_messages):
                    self.current_messages.pop(i)
                    self._refresh_advert_list_ui()

            btn_del = ctk.CTkButton(
                item, text="✕", width=24, height=24, font=get_font(10, "bold"),
                fg_color="transparent", hover_color=C_DANGER, text_color=C_DANGER,
                command=del_msg
            )
            btn_del.grid(row=0, column=2, padx=6, pady=4)

    def _add_advert_message(self):
        new_text = self.ent_new_ad.get().strip()
        if new_text:
            self.current_messages.append(new_text)
            self.ent_new_ad.delete(0, "end")
            self._refresh_advert_list_ui()

    def _reset_default_adverts(self):
        self.current_messages = list(DEFAULT_TABCHI_MESSAGES)
        self._refresh_advert_list_ui()

    def populate(self, settings: Settings):
        tab = settings.tabchi
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

        self.current_messages = list(tab.messages)
        self._refresh_advert_list_ui()

    def apply(self, settings: Settings):
        settings.tabchi.enabled = bool(self.sw_tabchi_enabled.get())
        try:
            settings.tabchi.min_interval_minutes = float(self.ent_tabchi_min.get())
            settings.tabchi.max_interval_minutes = float(self.ent_tabchi_max.get())
            settings.tabchi.dot_delay_seconds = float(self.ent_tabchi_dot_delay.get())
        except ValueError:
            pass

        settings.tabchi.randomize_interval = bool(self.sw_tabchi_random.get())
        settings.tabchi.order = self.seg_tabchi_order.get()
        settings.tabchi.anti_duplicate_dot = bool(self.sw_tabchi_dot.get())
        settings.tabchi.messages = list(self.current_messages)
