import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict

BASE_DIR = Path(__file__).parent.resolve()
SETTINGS_FILE = BASE_DIR / "settings.json"

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


@dataclass
class GameTypeDelay:
    """Per-game-type delay settings."""
    min_delay: float = 3.0
    max_delay: float = 7.0
    enabled: bool = True  # Whether to answer this game type at all


@dataclass
class StealthSettings:
    """Anti-cheat stealth configuration."""
    # Fake wrong attempts before correct answer
    fake_attempts_min: int = 0      # minimum wrong attempts (0 = sometimes no wrong attempt)
    fake_attempts_max: int = 2      # maximum wrong attempts
    fake_attempt_cooldown: float = 3.0  # seconds between each attempt (server cooldown)

    # Types of fake mistakes
    typo_nearby_keys: bool = True     # Replace chars with nearby keyboard chars
    typo_swap_case: bool = True       # Start with lowercase when original is uppercase
    typo_partial_word: bool = True    # Send only first part of the answer
    typo_reversed_word: bool = True   # Send a word reversed
    typo_missing_chars: bool = True   # Drop a few characters


@dataclass
class Settings:
    """All bot settings, persisted to settings.json."""
    # General
    player_username: str = "ItsReZNuM"
    dry_run: bool = False
    require_focus: bool = True
    send_method: str = "paste"        # "paste" or "write"
    chat_key: str = "t"
    send_cooldown: float = 3.0
    post_open_chat_delay: float = 0.25
    post_type_delay: float = 0.10
    max_candidate_retries: int = 2

    # Global delays (fallback if per-game-type not set)
    global_min_delay: float = 3.0
    global_max_delay: float = 7.0

    # Answer frequency: answer 1 out of every N games
    answer_ratio: int = 1

    # Guess number mode
    guess_number_mode: str = "random"  # "random" or "skip"

    # Auto-learn settings
    auto_learn_words: bool = True
    auto_learn_min_length: int = 3
    auto_learn_filter_random: bool = True

    # Stealth / Anti-cheat
    stealth: StealthSettings = field(default_factory=StealthSettings)

    # Per-game-type delays
    game_delays: Dict[str, GameTypeDelay] = field(default_factory=dict)

    def __post_init__(self):
        # Initialize default game delays for any missing types
        for gt in GAME_TYPES:
            if gt not in self.game_delays:
                self.game_delays[gt] = GameTypeDelay()
        # Convert dicts back to dataclass instances if loaded from JSON
        if isinstance(self.stealth, dict):
            self.stealth = StealthSettings(**self.stealth)
        for k, v in list(self.game_delays.items()):
            if isinstance(v, dict):
                self.game_delays[k] = GameTypeDelay(**v)

    def get_delay(self, game_type: str) -> tuple:
        """Returns (min_delay, max_delay) for a specific game type."""
        gt = game_type.lower()
        if gt in self.game_delays:
            gd = self.game_delays[gt]
            return (gd.min_delay, gd.max_delay)
        return (self.global_min_delay, self.global_max_delay)

    def is_game_type_enabled(self, game_type: str) -> bool:
        """Check if a game type is enabled for answering."""
        gt = game_type.lower()
        if gt in self.game_delays:
            return self.game_delays[gt].enabled
        return True

    def save(self, path: Path = None):
        """Save settings to JSON file."""
        save_path = path or SETTINGS_FILE
        data = asdict(self)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Path = None) -> "Settings":
        """Load settings from JSON file, falling back to defaults."""
        load_path = path or SETTINGS_FILE
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
