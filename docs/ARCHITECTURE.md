# MythoriaSolver Architecture & System Design

MythoriaSolver is a high-performance, automated Minecraft SMP chat game bot engineered in Python. It monitors Minecraft server logs in real-time, recognizes game challenge events via regular expressions, solves mathematical, textual, and trivia puzzles in sub-millisecond time, applies human-like stealth heuristics (typos, delay curves, fake mistakes), and dispatches answers via simulated keyboard input or clipboard injection.

---

## 1. High-Level System Architecture

```mermaid
flowchart TD
    subgraph Minecraft Server & Client
        MCLog[("Minecraft Client<br/>latest.log")] -->|Appends line| LogReader["minecraft.log_reader<br/>LogReader (Tailing)"]
        Sender["minecraft.sender<br/>AnswerSender"] -->|Win32 Key Simulation| MCWindow["Minecraft Game Window<br/>(Win32 Focus Check)"]
    end

    subgraph Core Pipeline (Background Thread)
        LogReader -->|Raw Text Line| ChatParser["minecraft.chat_parser<br/>ChatParser (Regex Engine)"]
        ChatParser -->|ChatGameQuestionEvent| Bot["main.py<br/>MinecraftChatBot Pipeline"]
        ChatParser -->|ChatGameEndEvent| Bot
        
        Bot -->|Extract Question & Context| Router["solver.router<br/>SolverRouter"]
        
        Router -->|Dispatch| Solvers["7 Specialized Solvers<br/>(Math, Scramble, Trivia, etc.)"]
        Solvers -->|Indexed Queries| DB[("database.models<br/>SQLite Database")]
        Solvers -->|Candidate List| Router
        
        Router -->|Ranked Candidates| Bot
        Bot -->|Filter & Plan Mistakes| Stealth["stealth.py<br/>Stealth Anti-Cheat Planner"]
        Stealth -->|Fake Typos + True Answer| Scheduler["Delay & Cooldown Manager"]
        Scheduler -->|Timed Dispatch| Sender
    end

    subgraph Tabchi Advertiser (Background Loop)
        TabchiLoop["tab.py / main.py<br/>Auto-Advertiser Timer"] -->|Auction Message| Sender
    end

    subgraph User Interface (Main Thread)
        Bot -.->|Event Queue Bridge| GUI["gui.py / ui.tabs.*<br/>CustomTkinter Modern GUI"]
        GUI -->|Configure & Persist| SettingsFile[("%APPDATA%/MythoriaSolver/<br/>settings.json")]
        SettingsFile -.->|Loaded by| Bot
    end
```

---

## 2. Concurrency & Threading Model

The application uses an asynchronous, multi-threaded architecture with strict separation of concerns:

1. **GUI Main Thread (`MythoriaGUI`):**
   - Owns the Tkinter / CustomTkinter event loop (`app.mainloop()`).
   - All UI rendering, window management, and widget interactions occur strictly on this thread.
   - Polls a thread-safe `queue.Queue` every 50ms (`self.after(50, self._process_event_queue)`) to receive telemetry from the background bot worker without blocking or causing UI freezes.

2. **Bot Worker Thread (`MinecraftChatBot.run()`):**
   - Spawns as a `daemon=True` thread when the user clicks **START BOT**.
   - Runs an event loop tailing `latest.log`.
   - Never touches Tkinter widgets directly; emits events through an `event_callback` closure pushing to the GUI `event_queue`.

3. **Log Reader Loop:**
   - Employs a non-blocking `seek`/`readline` tailing loop over `latest.log`.
   - Detects file rotations (e.g. game client restarts or truncation) and re-opens file handles seamlessly.

4. **Tabchi Advertising Timer:**
   - Evaluates elapsed minutes against randomized or fixed intervals.
   - Automatically interleaves advertisement messages with game answers respecting the 3.0-second server chat cooldown.

---

## 3. Directory Layout & Module Responsibilities

```
MythoriaSolver/
├── main.py                     # Central bot pipeline coordinator & CLI entry point
├── gui.py                      # Master CustomTkinter GUI window & navigation
├── config.py                   # Global environment paths, assets, and base directories
├── settings.py                 # Dataclasses & persistent JSON configuration (%APPDATA%)
├── stealth.py                  # Human typo generator, fake attempts planner, noise filter
├── tab.py                      # Tabchi auto-advertiser helper functions
│
├── ui/                         # Modular CustomTkinter GUI Components
│   ├── theme.py                # JetBrains Mono fonts, Obsidian dark palette, icon loader
│   ├── components.py           # Standardized cards, setting rows, switches, stat cards
│   └── tabs/                   # Dedicated modular tab views:
│       ├── dashboard.py        # Live monitoring, control bar, live terminal log, telemetry
│       ├── general.py          # Player name, log path selector, keyboard timings, ratios
│       ├── solvers.py          # Fallback delays, per-type toggles, auto-learning options
│       ├── stealth.py          # Fake wrong attempts, cooldowns, typo heuristic checkboxes
│       ├── tabchi.py           # Auto-advertiser timings, duplicate bypass, message pool
│       └── sandbox.py          # Instant interactive solver test playground & DB analytics
│
├── solver/                     # Puzzle Heuristic Engines
│   ├── router.py               # Auto-detection, routing, scoring, and candidate ranking
│   ├── math_solver.py          # Safe AST arithmetic solver with operator precedence
│   ├── scramble_solver.py      # Character signature hash anagram solver
│   ├── reverse_solver.py       # Unicode-safe string reversal
│   ├── trivia_solver.py        # Exact + RapidFuzz fuzzy question matching
│   ├── number_solver.py        # Guess-the-number range parser & search strategies
│   └── fill_solver.py          # Wildcard pattern solver (c_w -> cow)
│
├── minecraft/                  # Minecraft Client Integration
│   ├── chat_parser.py          # Regex event parser for SMP chat games and winner announcements
│   ├── log_finder.py           # Automatic launcher detector (CurseForge, Prism, Modrinth, etc.)
│   ├── log_reader.py           # Real-time tailing reader for latest.log
│   └── sender.py               # Low-level Win32 keyboard typing & clipboard injection
│
├── database/                   # Persistent Data Storage
│   ├── models.py               # SQLite DatabaseManager (items, trivia, stats)
│   └── minecraft_clean.db      # Pre-indexed SQLite database of 1,200+ Minecraft items
│
├── assets/                     # Assets & Resources
│   ├── icons/                  # 64x64 PNG antialiased vector icons (dashboard, settings, etc.)
│   ├── app_icon.ico            # Windows executable window icon
│   └── app_icon.png            # High-resolution application brand mark
│
├── docs/                       # Comprehensive Architecture & Agent Guides
└── tests/                      # Full Pytest Test Suite
```

---

## 4. Data Flow: From Chat Log to Chat Game Win

1. **Emission:** Minecraft client appends a chat line to `latest.log`.
2. **Read:** `LogReader` yields the line to `MinecraftChatBot`.
3. **Parse:** `ChatParser.parse_line()` matches known regex patterns.
   - If a game starts -> emits `ChatGameQuestionEvent(game_number, raw_type, question)`.
   - If a game ends -> emits `ChatGameEndEvent(winner, answer, our_won, duration)`.
4. **Solve:** `SolverRouter.solve(raw_type, question)` queries the appropriate solver.
5. **Stealth:** `plan_fake_attempts()` determines whether to send 0-2 deliberate typos first.
6. **Delay:** Sleep for the configured human reaction delay (`game_delays[type].sample()`).
7. **Verify:** Check if the game has already been won by another player while waiting.
8. **Focus Check:** Verify Minecraft HWND is active (if `require_focus=True`).
9. **Dispatch:** `AnswerSender.send()` opens chat with `chat_key` ('t'), pastes or types the answer, and presses Enter.
10. **Feedback:** Event emitted to GUI event queue; live stats and terminal feed updated.
