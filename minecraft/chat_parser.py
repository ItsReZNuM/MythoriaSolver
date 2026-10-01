import re
from dataclasses import dataclass
from typing import Optional, Union
from datetime import datetime


@dataclass
class ChatGameQuestionEvent:
    game_type: str
    clean_question: str
    raw_question: str
    timestamp: str


@dataclass
class ChatGameEndEvent:
    winner: Optional[str]
    duration_seconds: Optional[float]
    answer: Optional[str]
    timeout: bool
    timestamp: str


class ChatParser:
    """
    Parses Minecraft chat log lines and extracts Chat Game events.
    Handles multi-line game notifications:
      Line 1: A chat game has begun! <Game Type>:
      Line 2: (blank chat)
      Line 3: ▶ <Question Text> ◀
    And end notifications:
      Winner: <Player> has won the chat game in <Duration>s!
      Word: ▶ The word was: <Word> ◀  or  ▶ The answer was: <Answer> ◀
    """

    RE_START_GAME = re.compile(
        r"A chat game has begun!\s*(.*?)(?::|$)", re.IGNORECASE
    )
    RE_QUESTION_LINE = re.compile(r"▶\s*(.*?)\s*◀")

    RE_WINNER = re.compile(
        r"([a-zA-Z0-9_]+)\s+has won the chat game in\s+([\d\.]+)s!", re.IGNORECASE
    )
    RE_TIMEOUT = re.compile(
        r"(?:Time is up!|Nobody won the chat game|No player\(s\) answered)", re.IGNORECASE
    )
    RE_CORRECT_ANSWER = re.compile(
        r"(?:The word was|The answer was):\s*(.*?)\s*(?:◀|$)", re.IGNORECASE
    )

    RE_LOG_TIMESTAMP = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]")

    def __init__(self):
        self._pending_game_type: Optional[str] = None
        self._pending_start_timestamp: Optional[str] = None
        self._pending_winner: Optional[str] = None
        self._pending_duration: Optional[float] = None
        self._pending_timeout: bool = False
        self._pending_end_lines_left: int = 0

    def _extract_timestamp(self, line: str) -> str:
        match = self.RE_LOG_TIMESTAMP.match(line)
        if match:
            return match.group(1)
        return datetime.now().strftime("%H:%M:%S")

    def _clean_chat_line(self, line: str) -> str:
        """Strip Minecraft log prefixes: [HH:MM:SS] [thread/INFO]: [System] [CHAT] ..."""
        if "[CHAT]" in line:
            return line.split("[CHAT]", 1)[1].strip()
        return line.strip()

    def parse_line(self, raw_line: str) -> Optional[Union[ChatGameQuestionEvent, ChatGameEndEvent]]:
        timestamp = self._extract_timestamp(raw_line)
        chat_content = self._clean_chat_line(raw_line)

        # 1. Check for game start header
        start_match = self.RE_START_GAME.search(chat_content)
        if start_match:
            self._pending_game_type = start_match.group(1).strip()
            self._pending_start_timestamp = timestamp
            return None

        # 2. Check for question line if a game just began
        if self._pending_game_type:
            q_match = self.RE_QUESTION_LINE.search(chat_content)
            if q_match:
                clean_q = q_match.group(1).strip()
                event = ChatGameQuestionEvent(
                    game_type=self._pending_game_type,
                    clean_question=clean_q,
                    raw_question=raw_line,
                    timestamp=self._pending_start_timestamp or timestamp,
                )
                self._pending_game_type = None
                self._pending_start_timestamp = None
                return event

        # 3. Check for winner
        win_match = self.RE_WINNER.search(chat_content)
        if win_match:
            self._pending_winner = win_match.group(1)
            self._pending_duration = float(win_match.group(2))
            self._pending_timeout = False
            self._pending_end_lines_left = 4  # Wait up to 4 lines for 'The word was:'
            return None

        # 4. Check for timeout
        if self.RE_TIMEOUT.search(chat_content):
            self._pending_winner = None
            self._pending_duration = None
            self._pending_timeout = True
            self._pending_end_lines_left = 4
            return None

        # 5. Check for answer line if winner/timeout is pending
        ans_match = self.RE_CORRECT_ANSWER.search(chat_content)
        if ans_match:
            answer_text = ans_match.group(1).strip()
            event = ChatGameEndEvent(
                winner=self._pending_winner,
                duration_seconds=self._pending_duration,
                answer=answer_text,
                timeout=self._pending_timeout,
                timestamp=timestamp,
            )
            self._pending_winner = None
            self._pending_duration = None
            self._pending_timeout = False
            self._pending_end_lines_left = 0
            return event

        # Decrement wait counter if pending end
        if self._pending_end_lines_left > 0:
            self._pending_end_lines_left -= 1
            if self._pending_end_lines_left == 0 and (self._pending_winner or self._pending_timeout):
                # Flushed without explicit answer line
                event = ChatGameEndEvent(
                    winner=self._pending_winner,
                    duration_seconds=self._pending_duration,
                    answer=None,
                    timeout=self._pending_timeout,
                    timestamp=timestamp,
                )
                self._pending_winner = None
                self._pending_duration = None
                self._pending_timeout = False
                return event

        return None
