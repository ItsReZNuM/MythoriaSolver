"""
Unit Tests for Minecraft Chat Parser
Tests log line interpretation, event triggering, and legacy color code stripping.
"""
import pytest
from minecraft.chat_parser import ChatParser, ChatGameQuestionEvent, ChatGameEndEvent


class TestChatParser:
    def setup_method(self):
        self.parser = ChatParser()

    def test_question_event_detection(self):
        lines = [
            "[14:20:01] [Render thread/INFO]: [System] [CHAT] ⚑ CHAT GAMES",
            "[14:20:01] [Render thread/INFO]: [System] [CHAT] A chat game has begun! Unscramble the letters:",
            "[14:20:01] [Render thread/INFO]: [System] [CHAT] ▶ rTeppad etsCh ◀",
        ]
        events = []
        for l in lines:
            ev = self.parser.parse_line(l)
            if ev:
                events.append(ev)

        assert len(events) == 1
        ev = events[0]
        assert isinstance(ev, ChatGameQuestionEvent)
        assert ev.game_type == "Unscramble the letters"
        assert ev.clean_question == "rTeppad etsCh"

    def test_winner_event_detection(self):
        lines = [
            "[14:20:07] [Render thread/INFO]: [System] [CHAT] Notch has won the chat game in 3.42s!",
            "[14:20:07] [Render thread/INFO]: [System] [CHAT] ▶ The word was: Trapped Chest ◀",
        ]
        events = []
        for l in lines:
            ev = self.parser.parse_line(l)
            if ev:
                events.append(ev)

        assert len(events) == 1
        ev = events[0]
        assert isinstance(ev, ChatGameEndEvent)
        assert ev.winner == "Notch"
        assert ev.duration_seconds == 3.42
        assert ev.answer == "Trapped Chest"
        assert ev.timeout is False

    def test_irrelevant_chat_lines_ignored(self):
        noisy_lines = [
            "[14:20:00] [Render thread/INFO]: [CHAT] <Alex> Hello everyone!",
            "[14:20:01] [Render thread/INFO]: [CHAT] Steve fell from a high place",
            "[14:20:02] [Render thread/INFO]: Setting user: Notch",
            "",
            "Random text",
        ]
        for line in noisy_lines:
            assert self.parser.parse_line(line) is None
