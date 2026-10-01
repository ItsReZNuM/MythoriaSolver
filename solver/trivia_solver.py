import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import config

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None


class TriviaSolver:
    """
    Solves 'Answer the following' Minecraft server trivia questions.
    Uses cached Q&A pairs collected from server logs and fuzzy question matching.
    """

    def __init__(self, cache_file: Optional[Path] = None):
        self.cache_file = cache_file or config.TRIVIA_CACHE_FILE
        self.qa_data: Dict[str, str] = {}
        self.load_cache()

    def load_cache(self) -> None:
        if self.cache_file and self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.qa_data = json.load(f)
            except Exception:
                self.qa_data = {}

    def save_cache(self) -> None:
        if self.cache_file:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.qa_data, f, indent=2, ensure_ascii=False)

    def learn_answer(self, question: str, answer: str) -> None:
        clean_q = question.strip()
        clean_a = answer.strip()
        if clean_q and clean_a:
            self.qa_data[clean_q] = clean_a
            self.save_cache()

    def solve(self, question: str, limit: int = 1) -> List[Dict[str, Any]]:
        clean_q = question.strip()
        if not clean_q or not self.qa_data:
            return []

        # 1. Exact match (case-insensitive)
        for q, a in self.qa_data.items():
            if q.lower() == clean_q.lower():
                return [{"answer": a, "score": 100.0, "type": "trivia_exact"}]

        # 2. Fuzzy match
        if fuzz:
            best_q = None
            best_ratio = 0.0
            for q in self.qa_data.keys():
                ratio = fuzz.ratio(clean_q.lower(), q.lower())
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_q = q

            if best_q and best_ratio >= 85.0:
                return [
                    {
                        "answer": self.qa_data[best_q],
                        "score": round(best_ratio, 1),
                        "type": "trivia_fuzzy",
                    }
                ]

        return []

    def close(self):
        pass
