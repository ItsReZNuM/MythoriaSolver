import os
import sys
from pathlib import Path
from dataclasses import dataclass

# Support PyInstaller frozen bundles and persistent directory locations
if getattr(sys, "frozen", False):
    EXE_DIR = Path(sys.executable).parent.resolve()
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", EXE_DIR)).resolve()
else:
    EXE_DIR = Path(__file__).parent.resolve()
    BUNDLE_DIR = EXE_DIR

BASE_DIR = EXE_DIR


@dataclass(frozen=True)
class Config:
    # ----------------------------------------------------
    # File Paths
    # ----------------------------------------------------
    BASE_DIR: Path = BASE_DIR
    BUNDLE_DIR: Path = BUNDLE_DIR
    ASSETS_DIR: Path = BUNDLE_DIR / "assets"
    DB_PATH: Path = BASE_DIR / "database" / "minecraft_clean.db"
    COLLECTOR_DIR: Path = BASE_DIR / "collector"
    COLLECTOR_LOG_FILE: Path = COLLECTOR_DIR / "chat_games.jsonl"
    TRIVIA_CACHE_FILE: Path = COLLECTOR_DIR / "trivia_cache.json"

    # Default Minecraft log path on Windows
    DEFAULT_MINECRAFT_LOG: Path = Path(
        os.path.expandvars(r"%APPDATA%\.minecraft\logs\latest.log")
    )

    # ----------------------------------------------------
    # Minecraft Interaction Settings
    # ----------------------------------------------------
    PLAYER_USERNAME: str = "Player"
    WINDOW_TITLE_KEYWORD: str = "Minecraft"
    REQUIRE_FOCUS: bool = True
    DRY_RUN: bool = False  # Set to True to log answers without physical keystrokes

    # Chat automation
    CHAT_KEY: str = "t"
    PRE_OPEN_CHAT_DELAY: float = 0.05
    POST_OPEN_CHAT_DELAY: float = 0.08
    POST_TYPE_DELAY: float = 0.05
    SEND_COOLDOWN: float = 3.0  # Server cooldown requirement: at least 3 seconds
    MAX_CANDIDATE_RETRIES: int = 2

    # Send method: "paste" (fastest + 100% case preserved), "write" (type chars)
    SEND_METHOD: str = "paste"

    # Stealth / Anti-ban human delays (seconds)
    MIN_ANSWER_DELAY: float = 2.0
    MAX_ANSWER_DELAY: float = 5.0

    # Answer Frequency: 1 out of N games (1 = answer all, 3 = answer 1 of 3)
    ANSWER_RATIO: int = 1

    # ----------------------------------------------------
    # Solver Configurations
    # ----------------------------------------------------
    GUESS_NUMBER_MODE: str = "random"  # "random" or "skip"
    MAX_CANDIDATES: int = 5
    SOLVER_TIMEOUT_SECONDS: float = 10.0


config = Config()
