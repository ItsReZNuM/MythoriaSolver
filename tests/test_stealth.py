"""
Unit Tests for Stealth Engine & Anti-Cheat Evasion
"""
import pytest
from settings import StealthSettings
from stealth import (
    generate_typo_answer,
    plan_fake_attempts,
    looks_like_random_string,
)


class TestStealthEngine:
    def test_generate_typo_answer(self):
        word = "diamond"
        typo = generate_typo_answer(word)
        assert isinstance(typo, str)
        assert len(typo) > 0

    def test_plan_fake_attempts_disabled(self):
        cfg = StealthSettings(fake_attempts_min=0, fake_attempts_max=0)
        fakes = plan_fake_attempts("diamond", cfg)
        assert fakes == []

    def test_plan_fake_attempts_range(self):
        cfg = StealthSettings(fake_attempts_min=1, fake_attempts_max=2)
        fakes = plan_fake_attempts("emerald", cfg)
        assert 1 <= len(fakes) <= 2
        for f in fakes:
            assert f.lower() != "emerald"

    def test_looks_like_random_string_genuine_words(self):
        real_names = [
            "Dead Bush",
            "Nether Brick Slab",
            "Cow",
            "Iron Ingot",
            "Zombie Pigman",
            "Creeper",
            "Eye of Ender",
        ]
        for name in real_names:
            assert looks_like_random_string(name) is False, f"Flagged real name as random: {name}"

    def test_looks_like_random_string_honeypot_strings(self):
        random_junk = [
            "84H2heqtC",
            "SWGihXI",
            "zK9xP2",
            "x7y8z9",
            "12345",
            "aBcDeF",
        ]
        for junk in random_junk:
            assert looks_like_random_string(junk) is True, f"Failed to identify random honeypot: {junk}"
