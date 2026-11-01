"""
Unit Tests for Tabchi Auto-Advertiser Logic
"""
import pytest
from settings import TabchiSettings, DEFAULT_TABCHI_MESSAGES


class TestTabchiSettings:
    def test_default_tabchi_settings(self):
        tab = TabchiSettings()
        assert tab.enabled is False
        assert tab.min_interval_minutes == 3.0
        assert tab.max_interval_minutes == 5.0
        assert tab.anti_duplicate_dot is True
        assert len(tab.messages) >= len(DEFAULT_TABCHI_MESSAGES)

    def test_message_rotation(self):
        tab = TabchiSettings(
            messages=["Msg 1", "Msg 2", "Msg 3"],
            order="cycle"
        )
        assert tab.messages[0] == "Msg 1"
        assert tab.messages[1] == "Msg 2"
        assert tab.messages[2] == "Msg 3"
