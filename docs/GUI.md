# Graphical User Interface (GUI) Guide

MythoriaSolver features a modern, responsive desktop interface built with **CustomTkinter** and styled with an Obsidian Dark Palette and **JetBrains Mono** typography.

---

## 1. Modular Architecture Overview

The GUI code is split cleanly between the coordinator window and dedicated tab components:

```
ui/
├── theme.py          # Colors, font helpers, and 64x64 PNG icon loader
├── components.py     # Reusable setting cards, entry rows, and switches
└── tabs/             # Individual tab view classes:
    ├── dashboard.py  # DashboardTab (live stats, bot control, terminal log)
    ├── general.py    # GeneralTab (player name, log path, delays)
    ├── solvers.py    # SolversTab (heuristics toggles, solver delay overrides)
    ├── stealth.py    # StealthTab (human typo parameters, mistake injection)
    ├── tabchi.py     # TabchiTab (auto-advertiser timing & message pool)
    └── sandbox.py    # SandboxTab (direct solver test sandbox & DB counts)
```

The coordinator class `MythoriaGUI` in `gui.py` handles:
- Window geometry and centering on the desktop.
- Sidebar navigation and status pills.
- Thread-safe event queue polling (`queue.Queue`).
- Centralized settings load/save delegation.

---

## 2. Startup Smoothing & Anti-Flicker Engineering

CustomTkinter applications on Windows can suffer from black canvas flashes and layout shifts during initialization as hundreds of canvas objects calculate their bounds.

MythoriaSolver completely eliminates this issue using a 3-step off-screen preparation sequence:

1. **Immediate Withdrawal:**
   ```python
   self.withdraw()  # Keeps window completely hidden from desktop
   ```
2. **Off-Screen Layout Construction:**
   - All frames, fonts, switches, and entries are constructed and packed off-screen.
   - `self.update_idletasks()` forces Windows DWM and Tkinter to compute exact bounding boxes, font dimensions, and canvas background fills without displaying partial renders.
3. **Smooth Reveal:**
   ```python
   self.after(20, self.deiconify)  # Reveals the fully rendered, perfectly centered window
   ```

---

## 3. Instant 0ms Tab Switching

Each tab inherits from either `ctk.CTkFrame` (Dashboard) or `ctk.CTkScrollableFrame` (Settings tabs).

### The Compound Widget Quirk:
In CustomTkinter, `CTkScrollableFrame` wraps an internal canvas inside `self._parent_frame`. Calling `tkraise()` directly on the scrollable frame does not raise its container above sibling frames.

### The Solution:
`MythoriaGUI.switch_tab(tab_id)` uses `grid()` and `grid_remove()`:
```python
for tid, frame in self.tab_frames.items():
    if tid == tab_id:
        frame.grid()  # Restores exact row/column/sticky geometry
        actual_widget = getattr(frame, "_parent_frame", frame)
        actual_widget.tkraise()
    else:
        frame.grid_remove()  # Unmaps inactive tab without destroying state
```
- **Zero lag:** Inactive tabs consume no drawing cycles.
- **Zero bleed-through:** Only one frame is mapped at any given time.

---

## 4. Standalone Executable Packaging

The project includes `MythoriaSolver.spec` for building a single-file executable using **PyInstaller**:
- **Bundled Resources:** Pre-indexed SQLite database (`database/minecraft_clean.db`), trivia cache (`collector/trivia_cache.json`), antialiased icons (`assets/icons/`), and application icon (`assets/app_icon.ico`).
- **Hidden Imports:** Dynamically collects all CustomTkinter assets, PIL plugins, `darkdetect`, and Win32 modules.
- **Console Mode:** `console=False` produces a clean, professional windowed application with no background terminal black box.
