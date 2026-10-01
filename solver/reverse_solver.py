import re
from typing import List, Dict, Any, Optional
from database.models import DatabaseManager, MinecraftName


class ReverseSolver:
    """
    Solves 'Unreverse the letters' Minecraft chat game questions.
    Example:
        'roodparT aicacA' -> 'Acacia Trapdoor'
        'attocarreT dezalG kniP' -> 'Pink Glazed Terracotta'
        'woC' -> 'Cow'
        'SWGihXI' -> 'IXhiGWS'
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()

    def solve(self, question: str, limit: int = 5) -> List[Dict[str, Any]]:
        clean_q = question.strip()
        if not clean_q:
            return []

        # Candidate 1: Full string reversal (reverses word order + letters inside each word)
        cand1 = clean_q[::-1]

        # Candidate 2: Word-by-word reversal without changing word order
        words = clean_q.split()
        cand2 = " ".join(w[::-1] for w in words)

        results: List[Dict[str, Any]] = []
        seen = set()

        def add_candidate(ans: str, base_score: float, matched_db: bool):
            if ans in seen:
                return
            seen.add(ans)
            results.append(
                {
                    "answer": ans,
                    "score": round(base_score, 1),
                    "matched_db": matched_db,
                }
            )

        # Check DB for Candidate 1 (Full reverse)
        norm1 = re.sub(r"[^a-z0-9]", "", cand1.lower())
        db_item1 = self.db.find_by_normalized(norm1)
        if db_item1:
            add_candidate(db_item1.display_name, 100.0, True)

        # Check DB for Candidate 2 (Word-only reverse)
        norm2 = re.sub(r"[^a-z0-9]", "", cand2.lower())
        db_item2 = self.db.find_by_normalized(norm2)
        if db_item2:
            add_candidate(db_item2.display_name, 95.0, True)

        # Always include the raw string reversal as candidate
        # (Essential for random strings like SWGihXI -> IXhiGWS)
        add_candidate(cand1, 90.0 if not db_item1 else 85.0, False)

        if cand2 != cand1:
            add_candidate(cand2, 80.0, False)

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def close(self):
        pass
