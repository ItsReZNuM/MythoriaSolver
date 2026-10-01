import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from minecraft.chat_parser import ChatParser, ChatGameQuestionEvent, ChatGameEndEvent


class TestChatParser(unittest.TestCase):
    def setUp(self):
        self.parser = ChatParser()

    def test_start_question_sequence(self):
        lines = [
            "[13:08:04] [Render thread/INFO]: [System] [CHAT] ⚑ CHAT GAMES",
            "[13:08:04] [Render thread/INFO]: [System] [CHAT] ",
            "[13:08:04] [Render thread/INFO]: [System] [CHAT] A chat game has begun! Unscramble the letters:",
            "[13:08:04] [Render thread/INFO]: [System] [CHAT] ",
            "[13:08:04] [Render thread/INFO]: [System] [CHAT] ▶ rTeppad etsCh ◀",
            "[13:08:04] [Render thread/INFO]: [System] [CHAT] ",
        ]

        events = []
        for line in lines:
            ev = self.parser.parse_line(line)
            if ev:
                events.append(ev)

        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], ChatGameQuestionEvent)
        self.assertEqual(events[0].game_type, "Unscramble the letters")
        self.assertEqual(events[0].clean_question, "rTeppad etsCh")
        self.assertEqual(events[0].timestamp, "13:08:04")

    def test_win_event_sequence(self):
        lines = [
            "[13:08:10] [Render thread/INFO]: [System] [CHAT] G0D_M_R has won the chat game in 6.83s!",
            "[13:08:10] [Render thread/INFO]: [System] [CHAT] ",
            "[13:08:10] [Render thread/INFO]: [System] [CHAT] ▶ The word was: Smithing Template ◀",
        ]

        events = []
        for line in lines:
            ev = self.parser.parse_line(line)
            if ev:
                events.append(ev)

        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], ChatGameEndEvent)
        self.assertEqual(events[0].winner, "G0D_M_R")
        self.assertEqual(events[0].duration_seconds, 6.83)
        self.assertEqual(events[0].answer, "Smithing Template")
        self.assertFalse(events[0].timeout)


if __name__ == "__main__":
    unittest.main()
