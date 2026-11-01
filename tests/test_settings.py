"""
Unit Tests for Settings Management & APPDATA Persistence
"""
import os
import json
import pytest
from pathlib import Path
from settings import (
    Settings,
    GameTypeDelay,
    StealthSettings,
    TabchiSettings,
    APPDATA_DIR,
    SETTINGS_FILE,
)


class TestSettings:
    def test_settings_appdata_paths(self):
        # Settings path must be under APPDATA, never in repository root
        expected_appdata = os.environ.get("APPDATA")
        assert expected_appdata in str(APPDATA_DIR)
        assert expected_appdata in str(SETTINGS_FILE)
        assert SETTINGS_FILE.name == "settings.json"

    def test_settings_serialization_roundtrip(self, tmp_path):
        test_file = tmp_path / "test_settings.json"

        s1 = Settings(
            player_username="HeroNotch",
            minecraft_log_path="C:/custom/latest.log",
            dry_run=True,
            require_focus=True,
            send_method="write",
            chat_key="y",
            send_cooldown=4.5,
            answer_ratio=2,
            guess_number_mode="binary_search",
        )
        s1.game_delays["math"] = GameTypeDelay(min_delay=2.0, max_delay=4.0, enabled=False)

        # Save to file
        s1.save(test_file)
        assert test_file.exists()

        # Load back
        s2 = Settings.load(test_file)
        assert s2.player_username == "HeroNotch"
        assert s2.minecraft_log_path == "C:/custom/latest.log"
        assert s2.dry_run is True
        assert s2.require_focus is True
        assert s2.send_method == "write"
        assert s2.chat_key == "y"
        assert s2.send_cooldown == 4.5
        assert s2.answer_ratio == 2
        assert s2.guess_number_mode == "binary_search"
        assert s2.game_delays["math"].enabled is False
        assert s2.game_delays["math"].min_delay == 2.0

    def test_active_log_path_fallback(self):
        s = Settings(minecraft_log_path="")
        p = s.get_active_log_path()
        assert isinstance(p, Path)
        assert p.name == "latest.log"
