"""
Stealth & Anti-Cheat Evasion Tab
Human typo simulation, mistake injection, and anti-ban mechanics.
"""
import customtkinter as ctk

from settings import Settings
from ui.components import (
    create_settings_section,
    add_entry_row,
    add_switch_row,
)


class StealthTab(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        # ── Section 1: Human Mistake Simulation ──
        s_stealth = create_settings_section(
            self, "HUMAN MISTAKE SIMULATION",
            "Deliberately sends 0-2 plausible wrong attempts before typing the correct answer to bypass anti-cheat heuristics"
        )
        self.ent_fake_min = add_entry_row(s_stealth, "Min Wrong Attempts", "Minimum fake typos to submit (0 = sometimes answers directly)")
        self.ent_fake_max = add_entry_row(s_stealth, "Max Wrong Attempts", "Maximum fake typos before submitting correct answer (0 = disabled)")
        self.ent_fake_cooldown = add_entry_row(s_stealth, "Fake Attempt Cooldown (Seconds)", "Delay between fake wrong attempts (server cooldown: 3.0s)")

        # ── Section 2: Typo Generation Patterns ──
        s_patterns = create_settings_section(
            self, "TYPO GENERATION PATTERNS",
            "Choose which real-world human mistake types to simulate"
        )
        self.sw_typo_keys = add_switch_row(s_patterns, "Keyboard Neighbor Typos (Accidental slip on adjacent QWERTY key)")
        self.sw_typo_case = add_switch_row(s_patterns, "Initial Swap Case (Starts with lowercase when uppercase expected)")
        self.sw_typo_part = add_switch_row(s_patterns, "Partial Word Submissions (Submits unfinished prefix before correcting)")
        self.sw_typo_rev = add_switch_row(s_patterns, "Reversed Word Submissions (Inverts characters accidentally)")
        self.sw_typo_miss = add_switch_row(s_patterns, "Missing Characters (Drops random letter as if in a rush)")

    def populate(self, settings: Settings):
        st = settings.stealth
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

    def apply(self, settings: Settings):
        try:
            settings.stealth.fake_attempts_min = int(self.ent_fake_min.get())
            settings.stealth.fake_attempts_max = int(self.ent_fake_max.get())
            settings.stealth.fake_attempt_cooldown = float(self.ent_fake_cooldown.get())
        except ValueError:
            pass

        settings.stealth.typo_nearby_keys = bool(self.sw_typo_keys.get())
        settings.stealth.typo_swap_case = bool(self.sw_typo_case.get())
        settings.stealth.typo_partial_word = bool(self.sw_typo_part.get())
        settings.stealth.typo_reversed_word = bool(self.sw_typo_rev.get())
        settings.stealth.typo_missing_chars = bool(self.sw_typo_miss.get())
