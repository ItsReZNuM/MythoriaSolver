"""
MythoriaSolver Reusable UI Components
Cards, Sections, Styled Inputs, and Toggles.
"""
import customtkinter as ctk
from ui.theme import (
    get_font,
    C_CARD,
    C_BORDER,
    C_TEXT,
    C_TEXT_MUTED,
    C_SUCCESS,
)


def create_settings_section(parent, title: str, subtitle: str = "") -> ctk.CTkFrame:
    """Creates a standardized dark card container with title, subtitle, and divider."""
    card = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=8, border_width=1, border_color=C_BORDER)
    card.pack(fill="x", pady=(0, 14))

    hdr = ctk.CTkFrame(card, fg_color="transparent")
    hdr.pack(fill="x", padx=14, pady=(12, 6))

    ctk.CTkLabel(hdr, text=title, font=get_font(13, "bold"), text_color=C_TEXT).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(hdr, text=subtitle, font=get_font(10), text_color=C_TEXT_MUTED).pack(anchor="w")

    sep = ctk.CTkFrame(card, height=1, fg_color=C_BORDER)
    sep.pack(fill="x", padx=14, pady=(4, 6))
    return card


def add_entry_row(parent, label: str, tooltip: str = "", width: int = 200) -> ctk.CTkEntry:
    """Creates a 2-column settings row: label + description on left, styled entry on right."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=14, pady=5)
    row.grid_columnconfigure(0, weight=1)

    title_box = ctk.CTkFrame(row, fg_color="transparent")
    title_box.grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(title_box, text=label, font=get_font(11, "bold"), text_color=C_TEXT).pack(anchor="w")
    if tooltip:
        ctk.CTkLabel(title_box, text=tooltip, font=get_font(10), text_color=C_TEXT_MUTED).pack(anchor="w")

    ent = ctk.CTkEntry(
        row, width=width, height=32, font=get_font(11),
        fg_color="#12151d", border_color=C_BORDER
    )
    ent.grid(row=0, column=1, sticky="e")
    return ent


def add_switch_row(parent, label: str) -> ctk.CTkSwitch:
    """Creates a full-width toggle switch with green accent."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=14, pady=5)
    sw = ctk.CTkSwitch(row, text=f"  {label}", font=get_font(11), progress_color=C_SUCCESS)
    sw.pack(anchor="w")
    return sw


def create_stat_card(parent, col: int, title: str, value: str, color: str) -> ctk.CTkLabel:
    """Creates a metric display card with title and large bold numeric value."""
    card = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=8, border_width=1, border_color=C_BORDER)
    card.grid(row=0, column=col, sticky="ew", padx=4)

    lbl_t = ctk.CTkLabel(card, text=title, font=get_font(10, "bold"), text_color=C_TEXT_MUTED)
    lbl_t.pack(anchor="w", padx=12, pady=(10, 2))

    lbl_v = ctk.CTkLabel(card, text=value, font=get_font(18, "bold"), text_color=color)
    lbl_v.pack(anchor="w", padx=12, pady=(0, 10))
    return lbl_v
