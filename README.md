# ⚡ MythoriaSolver

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()
[![Minecraft](https://img.shields.io/badge/Minecraft-Java%20Edition-green.svg)]()
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg)]()
[![License](https://img.shields.io/badge/License-MIT-orange.svg)]()

**MythoriaSolver** is a high-performance, intelligent automation bot designed to automatically detect, solve, and answer **Chat Games** on Minecraft Java Edition SMP servers (Fabric, Forge, Vanilla, TLauncher) in real-time.

It tails Minecraft's `latest.log`, identifies chat game announcements with zero memory lag, dispatches the puzzle to specialized solvers, and simulates natural human keyboard inputs directly into the Minecraft chat with advanced anti-cheat evasion.

Now featured with a **Modern Dark CustomTkinter Desktop GUI** styled with **JetBrains Mono** typography and crisp vector icons.

---

## 🖥️ Modern Dark GUI & 6 Dedicated Tabs

MythoriaSolver provides a complete, modern graphical interface built with `customtkinter`:

1. **Dashboard & Live Telemetry**:
   - Real-time terminal log viewer with syntax-highlighted events (Questions, Solvers, Typed answers, Winners).
   - Live Session Counter Cards: Games Detected, Games Won, Accuracy Rate, Tabchi Ads Dispatched.
   - Master Start/Stop Bot controls and log cleaner.
2. **General & Minecraft Configuration**:
   - In-game player identity and username tracking.
   - Active log path selector with file browser and **Auto-Detector** for all installed Minecraft clients.
   - Input simulation controls: Dry-Run mode, Require Focus, Send Method (`paste` / `write`), Chat Key, and Cooldown timings.
   - Answer ratio controls (1 of every $N$ games) and Guess Number strategy.
3. **Solvers & Delays**:
   - Global fallback response delays.
   - Individual enable/disable toggles and customizable min/max response delays for each of the 7 game types.
   - Self-learning engine toggles (min word length, random anti-bot string filter).
4. **Stealth & Anti-Cheat Evasion**:
   - Human typo simulation: Deliberately submits 0–2 plausible mistakes before the correct answer.
   - Configurable mistake patterns: QWERTY keyboard neighbor typos, swapped initial case, partial words, reversed words, dropped letters.
5. **Tabchi / Auto-Advertiser**:
   - Autonomous periodic promotional broadcasting (e.g. `/ah view ...`).
   - Minute-based randomized intervals, cycle vs random message dispatch, and anti-duplicate dot (`.`) bypass.
   - Interactive message manager (Add, Delete, Reset to defaults).
6. **Sandbox & Historical Analytics**:
   - Direct manual puzzle solver playground: test gap fills, scrambles, or math expressions instantly.
   - Persistent database statistics (2,590+ verified entries) and all-time win-rate metrics.

---

## 🚀 Key Features

### 🧩 7 Specialized Solvers
- **Fill the Gaps (`FillSolver`)**: Fast regex matching against a clean database of 2,590+ verified Minecraft blocks, items, and mobs.
- **Unscramble Letters (`ScrambleSolver`)**: Instant $O(1)$ anagram lookup using pre-computed sorted-letter hash indexes.
- **Unreverse Letters (`ReverseSolver`)**: Handles both full-string reversal and word-by-word reversal with database confirmation.
- **Solve Equations (`MathSolver`)**: Safe AST-based arithmetic expression parser supporting operators, negative numbers, and parentheses (no unsafe `eval`).
- **Type the Letters (`TypeLetters`)**: Verbatim character echo with case preservation.
- **Guess the Number (`NumberSolver`)**:
  - Automatically parses numerical bounds (e.g. `1-15`, `1-50`).
  - **Live Competitor Elimination**: Listens to chat in real-time; when another player guesses a number, that number is immediately removed from the candidate pool.
  - **Continuous Guessing**: Keeps trying remaining unguessed numbers every cooldown interval until the game ends.
- **Answer the Following (`TriviaSolver`)**: Pre-loaded with server-specific Q&A pairs from historical archives, featuring fuzzy-string matching and real-time self-learning.

### 📢 Tabchi / Auto-Advertiser
- **Custom Advertisement List**: Add, remove, and manage promotional or auction chat messages (`/ah view ...`) directly from the GUI.
- **Minute-Based Intervals**: Fully configurable delays between advertisements in **minutes** (e.g. 3.0 to 5.0 minutes).
- **Randomized Interval Range**: Option to randomize the time between advertisements to appear natural and evade automated spam detection.
- **Cycle or Random Dispatch**: Rotate messages sequentially or pick random entries from the pool.
- **Anti-Duplicate Dot Bypass**: Automatically sends a subtle dot `.` before duplicate advertisements (mirroring Minecraft anti-spam bypass techniques).
- **Chat Game Priority**: Auto-advertiser automatically pauses whenever a Chat Game is detected, ensuring 100% priority for quiz answering.

### 🛡️ Anti-Cheat & Stealth Evasion
- **Randomized Delays**: Configurable min/max delay per game type or globally.
- **Human Typo Simulation**: Deliberately submits 0–2 plausible mistakes (keyboard-neighbor typos, dropped letters, lowercase initials) before the correct answer.
- **Answer Ratio**: Set the bot to participate in only 1 out of every $N$ games to blend in with normal players.
- **Focus Verification**: Automatically ensures Minecraft (`javaw.exe`) is the active foreground window before sending keystrokes.
- **Server Cooldown Compliance**: Strictly enforces the server's 3-second message cooldown.

### ⌨️ Layout-Independent Hardware Typing
- Built with Windows `keybd_event` combining **Virtual-Key Codes** and **Hardware Scan Codes** (`SCAN_T = 0x14`, `SCAN_RETURN = 0x1C`).
- **100% immune to Windows keyboard layout**: Works identically whether your active system keyboard language is English, Persian, Arabic, or any other layout.

---

## 📁 Project Structure

```text
MythoriaSolver/
├── assets/
│   ├── icons/                  # High-resolution antialiased vector icons (PNG)
│   ├── app_icon.ico            # Windows application icon
│   └── app_icon.png            # Window brand graphic
├── collector/
│   ├── chat_game_collector.py  # Session tracking & win-rate metrics
│   └── trivia_cache.json       # Pre-loaded server trivia Q&A database
├── database/
│   ├── build_database.py       # Script to rebuild database from raw text files
│   ├── models.py               # DatabaseManager with O(1) in-memory indexes
│   └── minecraft_clean.db      # SQLite database (2,590+ verified entries)
├── minecraft/
│   ├── chat_parser.py          # Regex parser for multi-line chat game events
│   ├── log_finder.py           # Auto-detector & selector for multi-version Minecraft logs
│   ├── log_reader.py           # Real-time non-blocking tail of latest.log
│   └── sender.py               # Hardware scancode input simulator & focus checker
├── solver/
│   ├── fill_solver.py          # Gap fill solver
│   ├── math_solver.py          # AST math expression solver
│   ├── number_solver.py        # Guess-the-number solver with live elimination
│   ├── reverse_solver.py       # String reversal solver
│   ├── router.py               # Central question router and heuristic detector
│   ├── scramble_solver.py      # Sorted-letter anagram solver
│   ├── trivia_solver.py        # Trivia Q&A fuzzy solver
│   └── test_*.py               # Comprehensive unit tests for all solvers
├── config.py                   # PyInstaller bundle & persistent path configuration
├── settings.py                 # Mutable, persistent configuration manager
├── settings.json               # Saved user configuration
├── stealth.py                  # Typo generator and anti-cheat mechanics
├── gui.py                      # Modern CustomTkinter Graphical User Interface
├── menu.py                     # Interactive Rich TUI menu
├── main.py                     # Main application entry point (GUI / CLI)
├── MythoriaSolver.spec         # PyInstaller standalone build specification
├── requirements.txt            # Python dependencies
└── README.md
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- **Operating System**: Windows 10 / 11
- **Python**: 3.10, 3.11, or 3.12
- **Minecraft**: Java Edition (Fabric, Forge, Vanilla, TLauncher)

### 2. Clone the Repository
```bash
git clone https://github.com/ItsReZNuM/MythoriaSolver.git
cd MythoriaSolver
```

### 3. Create a Virtual Environment & Install Dependencies
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🎯 Usage

### 1. Standalone Executable (No Python Required)
Run the compiled standalone executable directly:
```powershell
.\dist\MythoriaSolver.exe
```

### 2. Launch GUI (Python)
Launch the modern CustomTkinter GUI directly:
```powershell
python main.py
```
Or:
```powershell
python gui.py
```

### 3. Launch CLI Mode
If you prefer running in the terminal with the Rich TUI menu:
```powershell
python main.py --cli
```

### Command-Line Arguments
```powershell
# Run in CLI mode
python main.py --cli

# Replay historical latest.log to test solvers against past games
python main.py --replay

# Run without opening the interactive startup menu in CLI
python main.py --cli --no-menu

# Specify a custom Minecraft latest.log path
python main.py --log-path "C:\Path\To\.minecraft\logs\latest.log"
```

---

## 📦 Building the Standalone `.exe`

To recompile the standalone `.exe` using PyInstaller:
```powershell
pyinstaller --noconfirm MythoriaSolver.spec
```
The output executable will be created in `dist/MythoriaSolver.exe`.

---

## 🧪 Running Unit Tests

Run the test suite to verify all solvers:
```powershell
python -m unittest discover -s solver -p "test_*.py" -v
```

---

## ⚖️ Disclaimer & License

This project is created for educational and reverse-engineering purposes. Please ensure your usage complies with the rules of the Minecraft servers you play on.

Distributed under the **MIT License**. See `LICENSE` for more information.
