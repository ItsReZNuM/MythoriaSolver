import json
import os
import sys
import shutil
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List

def get_appdata_dir() -> Path:
    """Return persistent configuration directory in %APPDATA%/MythoriaSolver."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            p = Path(appdata) / "MythoriaSolver"
            p.mkdir(parents=True, exist_ok=True)
            return p
    p = Path.home() / ".mythoria"
    p.mkdir(parents=True, exist_ok=True)
    return p

APPDATA_DIR = get_appdata_dir()
SETTINGS_FILE = APPDATA_DIR / "settings.json"

# Support PyInstaller frozen bundles and persistent directory locations
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent.resolve()
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR)).resolve()
else:
    BASE_DIR = Path(__file__).parent.resolve()
    BUNDLE_DIR = BASE_DIR

GAME_TYPES = ["fill", "scramble", "reverse", "math", "type_letters", "guess_number", "trivia"]

GAME_TYPE_LABELS = {
    "fill": "Fill the Gaps",
    "scramble": "Unscramble Letters",
    "reverse": "Unreverse Letters",
    "math": "Solve Equation",
    "type_letters": "Type the Letters",
    "guess_number": "Guess the Number",
    "trivia": "Answer the Following",
}

DEFAULT_TABCHI_MESSAGES = [
    "All view ah new item",
    "ALLL View ah pale oak off",
    "All ./ah view items",
    "All view my ah",
    "All creaking heart ah",
    "ah off khorde hamechi moft moft",
]


@dataclass
class GameTypeDelay:
    """Per-game-type delay settings."""
    min_delay: float = 3.0
    max_delay: float = 7.0
    enabled: bool = True  # Whether to answer this game type at all


@dataclass
class StealthSettings:
    """Anti-cheat stealth configuration."""
    fake_attempts_min: int = 0
    fake_attempts_max: int = 2
    fake_attempt_cooldown: float = 3.0
    typo_nearby_keys: bool = True
    typo_swap_case: bool = True
    typo_partial_word: bool = True
    typo_reversed_word: bool = True
    typo_missing_chars: bool = True


@dataclass
class TabchiSettings:
    """Auto-advertiser (تبچی) configuration."""
    enabled: bool = False
    messages: List[str] = field(default_factory=lambda: list(DEFAULT_TABCHI_MESSAGES))
    min_interval_minutes: float = 3.0
    max_interval_minutes: float = 5.0
    randomize_interval: bool = True
    order: str = "cycle"
    anti_duplicate_dot: bool = True
    dot_delay_seconds: float = 3.0


@dataclass
class Settings:
    """All bot settings, persisted to %APPDATA%/MythoriaSolver/settings.json."""
    # General
    player_username: str = "Player"
    minecraft_log_path: str = ""
    dry_run: bool = False
    require_focus: bool = True
    send_method: str = "paste"
    chat_key: str = "t"
    send_cooldown: float = 3.0
    post_open_chat_delay: float = 0.25
    post_type_delay: float = 0.10
    max_candidate_retries: int = 2

    # Global delays
    global_min_delay: float = 3.0
    global_max_delay: float = 7.0

    # Answer frequency
    answer_ratio: int = 1

    # Guess number mode
    guess_number_mode: str = "random"

    # Auto-learn settings
    auto_learn_words: bool = True
    auto_learn_min_length: int = 3
    auto_learn_filter_random: bool = True

    # Stealth / Anti-cheat
    stealth: StealthSettings = field(default_factory=StealthSettings)

    # Tabchi / Auto-Advertiser
    tabchi: TabchiSettings = field(default_factory=TabchiSettings)

    # Per-game-type delays
    game_delays: Dict[str, GameTypeDelay] = field(default_factory=dict)

    def __post_init__(self):
        for gt in GAME_TYPES:
            if gt not in self.game_delays:
                self.game_delays[gt] = GameTypeDelay()
        if isinstance(self.stealth, dict):
            self.stealth = StealthSettings(**self.stealth)
        if isinstance(self.tabchi, dict):
            self.tabchi = TabchiSettings(**self.tabchi)
        for k, v in list(self.game_delays.items()):
            if isinstance(v, dict):
                self.game_delays[k] = GameTypeDelay(**v)

    def get_delay(self, game_type: str) -> tuple:
        gt = game_type.lower()
        if gt in self.game_delays:
            gd = self.game_delays[gt]
            return (gd.min_delay, gd.max_delay)
        return (self.global_min_delay, self.global_max_delay)

    def is_game_type_enabled(self, game_type: str) -> bool:
        gt = game_type.lower()
        if gt in self.game_delays:
            return self.game_delays[gt].enabled
        return True

    def get_active_log_path(self) -> Path:
        if self.minecraft_log_path:
            p = Path(self.minecraft_log_path).expanduser().resolve()
            if p.is_file():
                return p
        return Path(os.path.expandvars(r"%APPDATA%\.minecraft\logs\latest.log"))

    def save(self, path: Path = None):
        """Save settings to JSON file in APPDATA."""
        save_path = path or SETTINGS_FILE
        save_path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Path = None) -> "Settings":
        """Load settings from JSON file in APPDATA, migrating legacy files if needed."""
        load_path = path or SETTINGS_FILE
        if not load_path.exists():
            # Check if root legacy settings.json exists to migrate
            root_legacy = BASE_DIR / "settings.json"
            if root_legacy.exists() and root_legacy.resolve() != load_path.resolve():
                try:
                    load_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(root_legacy, load_path)
                except Exception:
                    pass

            # Also check PyInstaller bundled settings
            if not load_path.exists() and getattr(sys, "frozen", False):
                bundle_settings = BUNDLE_DIR / "settings.json"
                if bundle_settings.exists() and bundle_settings != load_path:
                    try:
                        load_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(bundle_settings, load_path)
                    except Exception:
                        pass

            if not load_path.exists():
                s = cls()
                s.save(load_path)
                return s

        try:
            with open(load_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**data)
        except Exception:
            return cls()


# Global singleton
settings = Settings.load()
