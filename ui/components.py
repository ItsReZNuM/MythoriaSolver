"""
MythoriaSolver Reusable UI Components
Cards, Sections, Styled Inputs, Toggles, and Smooth Hardware-Synchronized Scrollable Frame.
"""
import time
import tkinter as tk
import customtkinter as ctk
from ui.theme import (
    get_font,
    C_BG,
    C_CARD,
    C_BORDER,
    C_TEXT,
    C_TEXT_MUTED,
    C_SUCCESS,
)


class SmoothScrollableFrame(ctk.CTkScrollableFrame):
    """
    Optimized scrollable frame with hardware-synchronized, throttled scrolling.
    Eliminates Tkinter Canvas bitblt ghosting, smeared duplicate text, and widget lag.
    """
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", C_BG)
        super().__init__(master, **kwargs)

        self._parent_canvas.configure(bg=C_BG)
        self._last_scroll_time = 0.0
        self._pending_scroll = None
        self._flush_job = None

        orig_yview = self._parent_canvas.yview

        def throttled_yview(action, *args):
            now = time.perf_counter()
            if action == "moveto":
                target = float(args[0])
                # Throttle to 60 FPS (16ms) to prevent event queue starvation
                if now - self._last_scroll_time >= 0.016:
                    self._last_scroll_time = now
                    orig_yview("moveto", target)
                    self._parent_canvas.update_idletasks()
                    self._pending_scroll = None
                else:
                    self._pending_scroll = target
                    if not self._flush_job:
                        self._flush_job = self.after(16, self._flush_scroll)
            else:
                orig_yview(action, *args)
                self._parent_canvas.update_idletasks()

        self._scrollbar.configure(command=throttled_yview)

        # Flush exact target when user releases the scrollbar thumb
        self._scrollbar.bind("<ButtonRelease-1>", lambda e: self._flush_scroll(), add="+")
        self._scrollbar._canvas.bind("<ButtonRelease-1>", lambda e: self._flush_scroll(), add="+")

    def _flush_scroll(self):
        if self._flush_job:
            try:
                self.after_cancel(self._flush_job)
            except Exception:
                pass
            self._flush_job = None

        if self._pending_scroll is not None:
            t = self._pending_scroll
            self._pending_scroll = None
            self._parent_canvas.yview("moveto", t)
            self._parent_canvas.update_idletasks()
            self._last_scroll_time = time.perf_counter()

    def _mouse_wheel_all(self, event):
        super()._mouse_wheel_all(event)
        self._parent_canvas.update_idletasks()


def create_settings_section(parent, title: str, subtitle: str = "") -> ctk.CTkFrame:
    """Creates a standardized dark card container with title, subtitle, and divider."""
    card = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=8, border_width=1, border_color=C_BORDER)
    card.pack(fill="x", pady=(0, 14))

    hdr = tk.Frame(card, bg=C_CARD)
    hdr.pack(fill="x", padx=14, pady=(12, 6))

    ctk.CTkLabel(hdr, text=title, font=get_font(13, "bold"), text_color=C_TEXT, fg_color=C_CARD).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(hdr, text=subtitle, font=get_font(10), text_color=C_TEXT_MUTED, fg_color=C_CARD).pack(anchor="w")

    sep = tk.Frame(card, height=1, bg=C_BORDER)
    sep.pack(fill="x", padx=14, pady=(4, 6))
    return card


def add_entry_row(parent, label: str, tooltip: str = "", width: int = 200) -> ctk.CTkEntry:
    """Creates a 2-column settings row: label + description on left, styled entry on right."""
    row = tk.Frame(parent, bg=C_CARD)
    row.pack(fill="x", padx=14, pady=5)
    row.grid_columnconfigure(0, weight=1)

    title_box = tk.Frame(row, bg=C_CARD)
    title_box.grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(title_box, text=label, font=get_font(11, "bold"), text_color=C_TEXT, fg_color=C_CARD).pack(anchor="w")
    if tooltip:
        ctk.CTkLabel(title_box, text=tooltip, font=get_font(10), text_color=C_TEXT_MUTED, fg_color=C_CARD).pack(anchor="w")

    ent = ctk.CTkEntry(
        row, width=width, height=32, font=get_font(11),
        fg_color="#12151d", border_color=C_BORDER
    )
    ent.grid(row=0, column=1, sticky="e")
    return ent


def add_switch_row(parent, label: str) -> ctk.CTkSwitch:
    """Creates a full-width toggle switch with green accent."""
    row = tk.Frame(parent, bg=C_CARD)
    row.pack(fill="x", padx=14, pady=5)
    sw = ctk.CTkSwitch(row, text=f"  {label}", font=get_font(11), progress_color=C_SUCCESS, fg_color=C_CARD)
    sw.pack(anchor="w")
    return sw


def create_stat_card(parent, col: int, title: str, value: str, color: str) -> ctk.CTkLabel:
    """Creates a metric display card with title and large bold numeric value."""
    card = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=8, border_width=1, border_color=C_BORDER)
    card.grid(row=0, column=col, sticky="ew", padx=4)

    lbl_t = ctk.CTkLabel(card, text=title, font=get_font(10, "bold"), text_color=C_TEXT_MUTED, fg_color=C_CARD)
    lbl_t.pack(anchor="w", padx=12, pady=(10, 2))

    lbl_v = ctk.CTkLabel(card, text=value, font=get_font(18, "bold"), text_color=color, fg_color=C_CARD)
    lbl_v.pack(anchor="w", padx=12, pady=(0, 10))
    return lbl_v
