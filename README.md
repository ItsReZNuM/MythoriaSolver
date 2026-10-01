# ⚡ MythoriaSolver

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()
[![Minecraft](https://img.shields.io/badge/Minecraft-Java%20Edition-green.svg)]()
[![License](https://img.shields.io/badge/License-MIT-orange.svg)]()

**MythoriaSolver** is a high-performance, intelligent automation bot designed to automatically detect, solve, and answer **Chat Games** on Minecraft Java Edition SMP servers (Fabric, Forge, Vanilla, TLauncher) in real-time.

It tails Minecraft's `latest.log`, identifies chat game announcements with zero memory lag, dispatches the puzzle to specialized solvers, and simulates natural human keyboard inputs directly into the Minecraft chat with advanced anti-cheat evasion.

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

### 🛡️ Anti-Cheat & Stealth Evasion
- **Randomized Delays**: Configurable min/max delay per game type or globally.
- **Human Typo Simulation**: Deliberately submits 0–2 plausible mistakes (keyboard-neighbor typos, dropped letters, lowercase initials) before the correct answer.
- **Answer Ratio**: Set the bot to participate in only 1 out of every $N$ games to blend in with normal players.
- **Focus Verification**: Automatically ensures Minecraft (`javaw.exe`) is the active foreground window before sending keystrokes.
- **Server Cooldown Compliance**: Strictly enforces the server's 3-second message cooldown.

### ⌨️ Layout-Independent Hardware Typing
- Built with Windows `keybd_event` combining **Virtual-Key Codes** and **Hardware Scan Codes** (`SCAN_T = 0x14`, `SCAN_RETURN = 0x1C`).
- **100% immune to Windows keyboard layout**: Works identically whether your active system keyboard language is English, Persian, Arabic, or any other layout.

### 🎮 Game-Style Interactive Menu
- Navigable Rich TUI menu: `Start` / `Settings` / `Exit`.
- All settings are saved automatically to `settings.json` across sessions.

---

## 📁 Project Structure

```text
MythoriaSolver/
├── collector/
│   ├── chat_game_collector.py  # Session tracking & win-rate metrics
│   └── trivia_cache.json       # Pre-loaded server trivia Q&A database
├── database/
│   ├── build_database.py       # Script to rebuild database from raw text files
│   ├── models.py               # DatabaseManager with O(1) in-memory indexes
│   └── minecraft_clean.db      # SQLite database (2,590+ verified entries)
├── minecraft/
│   ├── chat_parser.py          # Regex parser for multi-line chat game events
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
├── config.py                   # Static configuration and defaults
├── settings.py                 # Mutable, persistent configuration manager
├── settings.json               # Saved user configuration
├── stealth.py                  # Typo generator and anti-cheat mechanics
├── menu.py                     # Interactive Rich TUI menu
├── main.py                     # Main application entry point
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

### Start the Bot (with Interactive Menu)
```powershell
python main.py
```
Upon launching, the interactive menu allows you to:
1. **START BOT**: Launch monitoring and answering.
2. **SETTINGS**: Customize delays, stealth fakes, answer ratio, dry-run mode, and per-game-type settings.
3. **EXIT**: Close the application.

### Command-Line Arguments
You can also launch directly by skipping the menu:
```powershell
# Run in Dry-Run mode (solves and logs, without typing into Minecraft)
python main.py --dry-run

# Run without opening the interactive menu
python main.py --no-menu

# Replay historical latest.log to test solvers against past games
python main.py --replay

# Specify a custom Minecraft latest.log path
python main.py --log-path "C:\Path\To\.minecraft\logs\latest.log"
```

---

## ⚙️ Configuration Reference (`settings.json`)

| Setting | Type | Default | Description |
|---|---|---|---|
| `dry_run` | `bool` | `false` | When true, logs answers without physical keystrokes |
| `require_focus` | `bool` | `true` | Only types when Minecraft is in the foreground |
| `send_method` | `string` | `"paste"` | Method to submit answer (`"paste"` or `"write"`) |
| `send_cooldown` | `float` | `3.0` | Minimum seconds between chat messages |
| `post_open_chat_delay` | `float` | `0.35` | Delay after pressing 'T' before typing |
| `answer_ratio` | `int` | `1` | Answer 1 out of every $N$ games ($1$ = answer all) |
| `global_min_delay` | `float` | `3.0` | Minimum delay before answering (seconds) |
| `global_max_delay` | `float` | `7.0` | Maximum delay before answering (seconds) |
| `stealth.fake_attempts_max` | `int` | `2` | Max intentional wrong guesses sent first |
| `auto_learn_words` | `bool` | `true` | Automatically adds server-announced answers to DB |

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
