import re
import random
from typing import List, Dict, Any, Tuple, Optional


class NumberSolver:
    """
    Handles 'Guess the number' chat games.
    Extracts range (e.g. '1-15', '1-50') and produces shuffled candidates
    so the bot can repeatedly guess remaining numbers every 3s cooldown
    until someone wins or time runs out.
    """

    def __init__(self, mode: str = "random"):
        self.mode = mode

    def parse_range(self, question: str) -> Tuple[int, int]:
        """Extract (min_val, max_val) from question text."""
        clean_q = question.strip()
        match = re.search(r"(\d+)\s*-\s*(\d+)", clean_q)
        if match:
            min_v = int(match.group(1))
            max_v = int(match.group(2))
            if min_v > max_v:
                min_v, max_v = max_v, min_v
            return (min_v, max_v)
        return (1, 15)

    def solve(self, question: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        clean_q = question.strip()
        min_val, max_val = self.parse_range(clean_q)

        if self.mode == "skip":
            return []

        # Generate all numbers in range
        numbers = list(range(min_val, max_val + 1))
        # Randomly shuffle so guesses look human and unpredictable
        random.shuffle(numbers)

        if limit is not None:
            numbers = numbers[:limit]

        candidates = []
        for num in numbers:
            candidates.append(
                {
                    "answer": str(num),
                    "score": 50.0,
                    "type": "random_guess",
                    "range": (min_val, max_val),
                }
            )
        return candidates

    def close(self):
        pass
