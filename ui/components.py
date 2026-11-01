"""
MythoriaSolver Reusable UI Components
Cards, Sections, Styled Inputs, Toggles, and Smooth Hardware-Synchronized Scrollable Frame.
"""
import sys
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

# Win32 GDI Redraw flags to completely eradicate canvas bitblt ghosting & smeared duplicate text
HAS_WIN32 = False
if sys.platform == "win32":
    try:
        import win32gui
        import win32con
        HAS_WIN32 = True
        REDRAW_DRAG_FLAGS = win32con.RDW_INVALIDATE | win32con.RDW_ERASE | win32con.RDW_ALLCHILDREN
        REDRAW_RELEASE_FLAGS = REDRAW_DRAG_FLAGS | win32con.RDW_UPDATENOW
    except ImportError:
        HAS_WIN32 = False


class SmoothScrollableFrame(ctk.CTkScrollableFrame):
    """
    Hardware-synchronized, 0ms-latency scrollable frame on Windows.
    Completely eliminates Tkinter Canvas GDI BitBlt ghosting, lagging text, and duplicate copies.
    """
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", C_BG)
        super().__init__(master, **kwargs)

        self._parent_canvas.configure(bg=C_BG)
        self._canvas_hwnd = None
        orig_yview = self._parent_canvas.yview

        def sync_yview(action, *args):
            # 1. Execute canvas scroll in real-time (0ms delay - 1:1 tracking with mouse)
            orig_yview(action, *args)

            # 2. Invalidate canvas & all child windows to wipe GDI BitBlt trails instantly
            if HAS_WIN32:
                try:
                    if self._canvas_hwnd is None:
                        self._canvas_hwnd = self._parent_canvas.winfo_id()
                    win32gui.RedrawWindow(self._canvas_hwnd, None, None, REDRAW_DRAG_FLAGS)
                except Exception:
                    pass

        self._scrollbar.configure(command=sync_yview)

        def on_release(event=None):
            if HAS_WIN32:
                try:
                    if self._canvas_hwnd is None:
                        self._canvas_hwnd = self._parent_canvas.winfo_id()
                    win32gui.RedrawWindow(self._canvas_hwnd, None, None, REDRAW_RELEASE_FLAGS)
                except Exception:
                    pass

        self._scrollbar.bind("<ButtonRelease-1>", on_release, add="+")
        self._scrollbar._canvas.bind("<ButtonRelease-1>", on_release, add="+")

    def _mouse_wheel_all(self, event):
        super()._mouse_wheel_all(event)
        if HAS_WIN32:
            try:
                if self._canvas_hwnd is None:
                    self._canvas_hwnd = self._parent_canvas.winfo_id()
                win32gui.RedrawWindow(self._canvas_hwnd, None, None, REDRAW_DRAG_FLAGS)
            except Exception:
                pass

    def _fit_frame_dimensions_to_canvas(self, event):
        if self._orientation == "vertical":
            w = event.width if event and hasattr(event, "width") and event.width > 1 else self._parent_canvas.winfo_width()
            self._parent_canvas.itemconfigure(self._create_window_id, width=w)
        else:
            h = event.height if event and hasattr(event, "height") and event.height > 1 else self._parent_canvas.winfo_height()
            self._parent_canvas.itemconfigure(self._create_window_id, height=h)


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
