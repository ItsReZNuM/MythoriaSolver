import re
from typing import List, Dict, Any, Optional
from database.models import DatabaseManager
from solver.fill_solver import FillSolver
from solver.scramble_solver import ScrambleSolver
from solver.reverse_solver import ReverseSolver
from solver.math_solver import MathSolver
from solver.number_solver import NumberSolver
from solver.trivia_solver import TriviaSolver
from config import config


class SolverRouter:
    """
    Routes chat game questions to the appropriate solver based on game_type
    or automatic heuristic detection.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()
        self.fill_solver = FillSolver(self.db)
        self.scramble_solver = ScrambleSolver(self.db)
        self.reverse_solver = ReverseSolver(self.db)
        self.math_solver = MathSolver()
        self.number_solver = NumberSolver(mode=config.GUESS_NUMBER_MODE)
        self.trivia_solver = TriviaSolver()

    def detect_type(self, game_type_str: str, question: str) -> str:
        """Standardize detected game type."""
        gt_lower = game_type_str.lower().strip()

        if "fill" in gt_lower or "gap" in gt_lower:
            return "fill"
        elif "scramble" in gt_lower:
            return "scramble"
        elif "reverse" in gt_lower:
            return "reverse"
        elif "equation" in gt_lower or "math" in gt_lower or "solve" in gt_lower:
            return "math"
        elif "type" in gt_lower or "letter" in gt_lower:
            return "type_letters"
        elif "guess" in gt_lower or "number" in gt_lower:
            return "guess_number"
        elif "answer" in gt_lower or "following" in gt_lower:
            return "trivia"

        # Heuristic fallbacks from question content
        q = question.strip()
        if "_" in q:
            return "fill"
        if re.search(r"range of \d+-\d+", q, re.IGNORECASE):
            return "guess_number"
        if re.match(r"^[\d\s\+\-\*\/\(\)\.]+$", q) and any(c in q for c in "+-*/"):
            return "math"

        return "unknown"

    def solve(
        self, game_type_str: str, question: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        clean_q = question.strip()
        detected_type = self.detect_type(game_type_str, clean_q)

        candidates: List[Dict[str, Any]] = []
        solver_name = "None"

        if detected_type == "fill":
            solver_name = "FillSolver"
            candidates = self.fill_solver.solve(clean_q, limit=limit)

        elif detected_type == "scramble":
            solver_name = "ScrambleSolver"
            candidates = self.scramble_solver.solve(clean_q, limit=limit)

        elif detected_type == "reverse":
            solver_name = "ReverseSolver"
            candidates = self.reverse_solver.solve(clean_q, limit=limit)

        elif detected_type == "math":
            solver_name = "MathSolver"
            candidates = self.math_solver.solve(clean_q, limit=limit)

        elif detected_type == "type_letters":
            solver_name = "TypeLetters"
            candidates = [
                {
                    "answer": clean_q,
                    "score": 100.0,
                    "type": "type_letters",
                }
            ]

        elif detected_type == "guess_number":
            solver_name = "NumberSolver"
            candidates = self.number_solver.solve(clean_q, limit=max(limit, 50))

        elif detected_type == "trivia":
            solver_name = "TriviaSolver"
            candidates = self.trivia_solver.solve(clean_q, limit=limit)

        else:
            # Try guessing if unknown
            if "_" in clean_q:
                solver_name = "FillSolver"
                candidates = self.fill_solver.solve(clean_q, limit=limit)
            else:
                solver_name = "ReverseSolver"
                candidates = self.reverse_solver.solve(clean_q, limit=limit)

        for c in candidates:
            c["solver"] = solver_name
            c["detected_type"] = detected_type

        return candidates
