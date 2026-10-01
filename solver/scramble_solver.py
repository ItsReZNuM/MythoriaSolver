import re
from typing import List, Dict, Any, Optional
from database.models import DatabaseManager, MinecraftName


class ScrambleSolver:
    """
    Solves 'Unscramble the letters' Minecraft chat game questions.
    Example:
        'hticW' -> 'Witch'
        'maooBb oiMcsa aSsitr' -> 'Bamboo Mosaic Stairs'
        'rTeppad etsCh' -> 'Trapped Chest'
        'hriBc taBo ihwt stheC' -> 'Birch Boat with Chest'
        'iSmtghni eamltpeT' -> 'Smithing Template'
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()

    def solve(self, question: str, limit: int = 5) -> List[Dict[str, Any]]:
        clean_q = question.strip()
        if not clean_q:
            return []

        norm_q = re.sub(r"[^a-z0-9]", "", clean_q.lower())
        if not norm_q:
            return []

        q_sorted = "".join(sorted(norm_q))
        matching_items = self.db.find_by_sorted_letters(q_sorted)

        # Word-by-word signatures for finer disambiguation
        q_words = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in clean_q.split()]
        q_words = [w for w in q_words if w]
        q_word_sigs = sorted(["".join(sorted(w)) for w in q_words])

        results: List[Dict[str, Any]] = []
        for item in matching_items:
            score = 90.0

            # Compare word signatures
            cand_words = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in item.display_name.split()]
            cand_words = [w for w in cand_words if w]
            cand_word_sigs = sorted(["".join(sorted(w)) for w in cand_words])

            if q_word_sigs == cand_word_sigs:
                score += 10.0  # Exact word-by-word scramble match

            if len(item.display_name.split()) == len(clean_q.split()):
                score += 5.0

            if item.type == "server_verified":
                score += 2.0

            results.append(
                {
                    "answer": item.display_name,
                    "score": round(score, 1),
                    "type": item.type,
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def close(self):
        pass
