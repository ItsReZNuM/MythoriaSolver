import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from database.models import DatabaseManager, MinecraftName


class FillSolver:
    """
    Solves 'Fill the gaps' Minecraft chat game questions.
    Example:
        'Ne_h_r Br_c_ _la_' -> 'Nether Brick Slab'
        '__elot Sp_wn ___' -> 'Ocelot Spawn Egg'
        '_an_ro_e St___s' -> 'Mangrove Stairs'
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()

    def solve(self, question: str, limit: int = 5) -> List[Dict[str, Any]]:
        clean_q = question.strip()
        if not clean_q or "_" not in clean_q:
            return []

        # 1. Build regex matching display_name (preserves word spaces and lengths)
        display_pattern_parts = []
        for char in clean_q:
            if char == "_":
                display_pattern_parts.append(r"[a-zA-Z0-9']")
            elif char.isspace():
                display_pattern_parts.append(r"\s+")
            else:
                display_pattern_parts.append(re.escape(char))

        display_regex_str = "^" + "".join(display_pattern_parts) + "$"
        display_regex = re.compile(display_regex_str, re.IGNORECASE)

        # 2. Build fallback regex matching normalized_name (ignores spaces)
        norm_pattern_parts = []
        for char in clean_q:
            if char == "_":
                norm_pattern_parts.append(r"[a-z0-9]")
            elif char.isalnum():
                norm_pattern_parts.append(char.lower())

        norm_regex_str = "^" + "".join(norm_pattern_parts) + "$"
        norm_regex = re.compile(norm_regex_str)

        results: List[Dict[str, Any]] = []
        seen_names = set()

        q_len = len(clean_q)
        q_words = len(clean_q.split())

        for item in self.db.all_items:
            display_match = display_regex.match(item.display_name)
            norm_match = norm_regex.match(item.normalized_name)

            if display_match or norm_match:
                if item.display_name in seen_names:
                    continue
                seen_names.add(item.display_name)

                # Scoring
                score = 80.0
                if display_match:
                    score += 20.0
                if len(item.display_name) == q_len:
                    score += 10.0
                if item.word_count == q_words:
                    score += 5.0
                if item.type == "server_verified":
                    score += 3.0

                results.append(
                    {
                        "answer": item.display_name,
                        "score": round(score, 1),
                        "type": item.type,
                    }
                )

        # Sort results by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def close(self):
        pass