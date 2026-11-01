# Future Agent Onboarding & Development Guide

Welcome, Agent! This guide is written specifically for you or any future automated assistant working on **MythoriaSolver**. Follow these conventions and rules to maintain architectural integrity.

---

## 1. Core Invariants (Do Not Break)

1. **Settings Must Never Live in Root:**
   - All user configuration must reside in `%APPDATA%\MythoriaSolver\settings.json`.
   - Never write `settings.json` into the repository root. `config.py` defines `APPDATA_DIR` and `SETTINGS_FILE`.
2. **GUI Modular Separation:**
   - Never bloat `gui.py` with widget building code.
   - If adding controls to a tab, place them in the corresponding `ui/tabs/<tab>.py` class.
   - Implement both `populate(self, settings)` and `apply(self, settings)` in the tab class.
3. **No Direct Tkinter Calls from Worker Threads:**
   - Background threads (such as `MinecraftChatBot` or `Tabchi`) must never call Tkinter widget methods directly.
   - Always push events to `self.event_queue.put((event_type, data))` and let the main thread process them in `_process_event_queue()`.
4. **Window Flicker Prevention:**
   - Always keep `self.withdraw()` at the beginning of `MythoriaGUI.__init__()` and schedule `self.after(20, self.deiconify)` after `self.update_idletasks()`.
5. **Tab Switching Contract:**
   - Always use `grid()` and `grid_remove()`. Do not rely solely on `tkraise()` because `CTkScrollableFrame` compound widgets wrap their children inside `_parent_frame`.

---

## 2. How to Add a New Chat Game Solver

1. **Create Solver File:** Add `solver/<game>_solver.py` implementing a `solve(question: str) -> List[Dict[str, Any]]` function.
2. **Register in `settings.py`:**
   - Add the game key to `GAME_TYPES` tuple.
   - Add human-readable label to `GAME_TYPE_LABELS`.
   - Add default delay entry in `DEFAULT_GAME_DELAYS`.
3. **Register in `solver/router.py`:**
   - Import solver and instantiate in `SolverRouter.__init__()`.
   - Add detection regex in `detect_type()`.
   - Add dispatch branch in `solve()`.
4. **Register in `ui/tabs/solvers.py`:**
   - The UI automatically loops over `GAME_TYPES`, so your solver will immediately appear with a toggle and delay inputs!
5. **Add Pytest Tests:** Add unit tests in `tests/test_solvers.py`.

---

## 3. How to Add a New Chat Message Regex

In `minecraft/chat_parser.py`:
- Add the regex pattern to `QUESTION_PATTERNS` or `END_PATTERNS`.
- Ensure named capture groups match expected keys (`game_type`, `question`, `winner`, `answer`).
- Add sample log lines to `tests/test_chat_parser.py` to prevent regression.

---

## 4. How to Run Tests & Build Executable

### Running Unit & Integration Tests:
```powershell
.venv\Scripts\python.exe -m pytest tests/ -v
```

### Compiling Standalone `.exe`:
```powershell
# 1. Ensure no running instances hold a file lock
Stop-Process -Name *Mythoria* -Force -ErrorAction SilentlyContinue

# 2. Run PyInstaller
.venv\Scripts\pyinstaller.exe --noconfirm MythoriaSolver.spec

# 3. Output is written to:
# dist/MythoriaSolver.exe
```

### Git Commit Conventions:
Follow Conventional Commits:
- `feat(scope): ...` for new features
- `fix(scope): ...` for bug fixes
- `refactor(scope): ...` for architectural improvements
- `docs(scope): ...` for documentation additions
