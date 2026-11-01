# Minecraft Integration & Input Pipeline

This document explains how MythoriaSolver interfaces with the Minecraft client environment: reading live game logs, parsing events, detecting installed launchers, and simulating human-like keystrokes.

---

## 1. Real-Time Log Tailing (`minecraft/log_reader.py`)

The `LogReader` class tails Minecraft's active `latest.log` file in real time:

- **Non-blocking Tailing:**
  - Opens `latest.log` with `utf-8` encoding (with fallback to `cp1252` and `latin-1` if corrupted characters occur).
  - Starts by seeking to the end of the file (`seek(0, os.SEEK_END)`) so historical logs are not re-processed upon startup.
  - In `--replay` mode, reads from line 0 sequentially to simulate past games.
- **Rotation Resilience:**
  - Minecraft rotates or truncates `latest.log` when restarted or when zipped into `latest.log.gz`.
  - The reader checks inode/file size: if the current file size is smaller than the current offset, the file was truncated or recreated, so the reader transparently re-opens the file handle.

---

## 2. Chat Parser Engine (`minecraft/chat_parser.py`)

Minecraft log lines follow a standard timestamp format:
```
[14:23:05] [Render thread/INFO]: [CHAT] [Game] Unscramble: d i a m o n d
```

### Event Classes
- `ChatGameQuestionEvent`:
  - `game_number: int` (e.g. #42)
  - `raw_type: str` (e.g. `scramble`, `math`, `trivia`, `fill`)
  - `question: str` (raw unescaped question text)
  - `clean_question: str` (stripped of Minecraft formatting color codes `§a`, `§f`, etc.)
- `ChatGameEndEvent`:
  - `winner: str` (Player display name or None if skipped/timed out)
  - `answer: str` (The correct answer revealed by the server)
  - `our_won: bool` (True if our configured player username matches the winner)
  - `duration: float` (Time taken in seconds)

### Color Code Stripping
Minecraft chat messages frequently include legacy formatting codes (`§0` through `§f`, `§k`, `§l`, `§m`, `§n`, `§o`, `§r`). `ChatParser` strips these using regular expression:
```python
re.sub(r"§[0-9a-fk-or]", "", raw_line)
```

---

## 3. Cross-Launcher Auto-Detection (`minecraft/log_finder.py`)

MythoriaSolver automatically scans and detects all active Minecraft installations on Windows across standard and third-party launchers:

| Launcher | Scanned Default Directory |
| :--- | :--- |
| **Vanilla Minecraft** | `%APPDATA%\.minecraft\logs\latest.log` |
| **CurseForge** | `%USERPROFILE%\curseforge\minecraft\Instances\*\logs\latest.log` |
| **Prism Launcher** | `%APPDATA%\PrismLauncher\instances\*\.minecraft\logs\latest.log` |
| **Modrinth App** | `%APPDATA%\ModrinthApp\profiles\*\logs\latest.log` |
| **Feather Client** | `%APPDATA%\.feather\user-modded\*\logs\latest.log` |
| **Badlion Client** | `%APPDATA%\.badlion\minecraft\logs\latest.log` |
| **Lunar Client** | `%USERPROFILE%\.lunarclient\offline\multiver\logs\latest.log` |
| **MultiMC** | `%APPDATA%\MultiMC\instances\*\.minecraft\logs\latest.log` |

- **Sorting by Recency:** Discovered instances are returned sorted by `os.path.getmtime` descending, ensuring the currently running game client is presented at the top of the list.

---

## 4. Win32 Keyboard & Clipboard Sender (`minecraft/sender.py`)

`AnswerSender` dispatches the final computed answer to the Minecraft client:

### Focus Verification (`require_focus=True`)
Prevents typing in sensitive desktop applications if the user is alt-tabbed:
1. Calls Win32 API `win32gui.GetForegroundWindow()`.
2. Inspects `win32gui.GetWindowText(hwnd).lower()`.
3. Ensures `"minecraft"` is in the window title before sending keystrokes.

### Send Methods:
1. **Clipboard Pasting (`send_method="paste"` - Recommended):**
   - Copies the answer to the system clipboard via `pyperclip.copy(answer)`.
   - Presses `chat_key` (default: `'t'`).
   - Waits `post_open_chat_delay` (default: 0.25s).
   - Presses `Ctrl + V` via Win32 key events.
   - Waits `post_type_delay` (default: 0.10s).
   - Presses `Enter`.
   - *Advantages:* Immune to keyboard layout mismatches (Persian, Cyrillic, QWERTZ) and instantaneous.

2. **Simulated Keystroke Typing (`send_method="write"`):**
   - Types characters sequentially via `pyautogui.typewrite(answer, interval=0.02)`.
   - Simulates realistic human typing cadence character-by-character.
