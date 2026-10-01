import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from config import config


@dataclass
class ChatGameRecord:
    timestamp: str
    game_type: str
    question: str
    candidates: List[Dict[str, Any]]
    answer_sent: Optional[str]
    actual_answer: Optional[str] = None
    winner: Optional[str] = None
    win_duration: Optional[float] = None
    is_correct: bool = False
    our_bot_won: bool = False
    notes: str = ""


class ChatGameCollector:
    """
    Collects and logs chat game sessions for performance tracking and self-learning.
    Saves records as structured JSONL.
    """

    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or config.COLLECTOR_LOG_FILE
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.active_session: Optional[ChatGameRecord] = None

    def start_session(
        self,
        timestamp: str,
        game_type: str,
        question: str,
        candidates: List[Dict[str, Any]],
        answer_sent: Optional[str] = None,
    ) -> ChatGameRecord:
        record = ChatGameRecord(
            timestamp=timestamp,
            game_type=game_type,
            question=question,
            candidates=candidates,
            answer_sent=answer_sent,
        )
        self.active_session = record
        return record

    def record_answer_sent(self, answer: str) -> None:
        if self.active_session:
            self.active_session.answer_sent = answer

    def complete_session(
        self,
        winner: Optional[str] = None,
        duration: Optional[float] = None,
        actual_answer: Optional[str] = None,
        player_username: Optional[str] = None,
    ) -> Optional[ChatGameRecord]:
        if not self.active_session:
            return None

        record = self.active_session
        record.winner = winner
        record.win_duration = duration
        record.actual_answer = actual_answer

        player_name = player_username or config.PLAYER_USERNAME

        # Check if our answer was mathematically/factually correct
        if (
            record.answer_sent
            and actual_answer
            and record.answer_sent.strip().lower() == actual_answer.strip().lower()
        ):
            record.is_correct = True

        # Check if our bot was the official winner recorded by the server
        if winner and player_name and winner.lower() == player_name.lower():
            record.our_bot_won = True

        self._save_record(record)
        self.active_session = None
        return record

    def _save_record(self, record: ChatGameRecord) -> None:
        try:
            line = json.dumps(asdict(record), ensure_ascii=False)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        """Calculates win rate and game statistics from collected JSONL."""
        if not self.log_file.exists():
            return {"total_games": 0, "won_games": 0, "win_rate_pct": 0.0, "avg_win_duration": 0.0}

        total = 0
        won = 0
        correct = 0
        durations = []

        with open(self.log_file, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    total += 1
                    if data.get("our_bot_won"):
                        won += 1
                    if data.get("is_correct") or (
                        data.get("answer_sent")
                        and data.get("actual_answer")
                        and data["answer_sent"].strip().lower()
                        == data["actual_answer"].strip().lower()
                    ):
                        correct += 1
                    dur = data.get("win_duration")
                    if dur:
                        durations.append(dur)
                except Exception:
                    pass

        avg_dur = sum(durations) / len(durations) if durations else 0.0
        return {
            "total_games": total,
            "won_games": won,
            "correct_answers": correct,
            "accuracy_pct": round((correct / total * 100), 1) if total else 0.0,
            "win_rate_pct": round((won / total * 100), 1) if total else 0.0,
            "avg_win_duration": round(avg_dur, 2),
        }
