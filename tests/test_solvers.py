"""
Unit Tests for Solvers Engine & Router
Tests each of the 7 individual solvers and the SolverRouter heuristic engine.
"""
import pytest
from solver.math_solver import MathSolver
from solver.reverse_solver import ReverseSolver
from solver.fill_solver import FillSolver
from solver.scramble_solver import ScrambleSolver
from solver.number_solver import NumberSolver
from solver.trivia_solver import TriviaSolver
from solver.router import SolverRouter


# ── Math Solver Tests ────────────────────────────────────────────────────────
class TestMathSolver:
    def setup_method(self):
        self.solver = MathSolver()

    def test_basic_arithmetic(self):
        cases = [
            ("2 + 2", "4"),
            ("100 - 35", "65"),
            ("6 * 7", "42"),
            ("144 / 12", "12"),
            ("10 % 3", "1"),
            ("2 ** 5", "32"),
        ]
        for expr, expected in cases:
            res = self.solver.solve(expr)
            assert len(res) == 1, f"Failed on {expr}"
            assert res[0]["answer"] == expected

    def test_operator_precedence(self):
        res = self.solver.solve("2 + 3 * 4")
        assert res[0]["answer"] == "14"

        res_paren = self.solver.solve("(2 + 3) * 4")
        assert res_paren[0]["answer"] == "20"

    def test_negative_numbers(self):
        cases = [
            ("-10 * -2", "20"),
            ("-4 - (-6) + (-9) - (-1)", "-6"),
            ("2 + 0 * 5 - 2", "0"),
        ]
        for expr, expected in cases:
            res = self.solver.solve(expr)
            assert res[0]["answer"] == expected

    def test_invalid_syntax_safe_rejection(self):
        invalid_cases = [
            "",
            "   ",
            "import os; os.system('echo 1')",
            "__import__('sys').exit()",
            "2 + +",
            "abc + def",
        ]
        for bad in invalid_cases:
            res = self.solver.solve(bad)
            assert res == [], f"Expected empty list for unsafe or invalid: {bad}"


# ── Reverse Solver Tests ─────────────────────────────────────────────────────
class TestReverseSolver:
    def test_simple_reverse(self, db_manager):
        solver = ReverseSolver(db_manager)
        res = solver.solve("woC")
        assert len(res) >= 1
        answers = [c["answer"].lower() for c in res]
        assert "cow" in answers

    def test_reverse_with_spaces(self, db_manager):
        solver = ReverseSolver(db_manager)
        res = solver.solve("w o B")
        assert len(res) >= 1
        assert any("bow" in c["answer"].lower() for c in res)


# ── Fill Solver Tests ────────────────────────────────────────────────────────
class TestFillSolver:
    def test_wildcard_patterns(self, db_manager):
        solver = FillSolver(db_manager)
        res = solver.solve("c_w")
        assert len(res) >= 1
        answers = [c["answer"].lower() for c in res]
        assert "cow" in answers

    def test_length_enforcement(self, db_manager):
        solver = FillSolver(db_manager)
        res = solver.solve("d_am_nd")
        assert len(res) >= 1
        answers = [c["answer"].lower() for c in res]
        assert "diamond" in answers


# ── Scramble Solver Tests ────────────────────────────────────────────────────
class TestScrambleSolver:
    def test_anagram_lookup(self, db_manager):
        solver = ScrambleSolver(db_manager)
        res = solver.solve("p a l p e")
        assert len(res) >= 1
        answers = [c["answer"].lower() for c in res]
        assert "apple" in answers


# ── Number Guessing Solver Tests ─────────────────────────────────────────────
class TestNumberSolver:
    def test_range_parsing(self):
        solver = NumberSolver(mode="all")
        min_v, max_v = solver.parse_range("Guess a number in the range of 1-5")
        assert (min_v, max_v) == (1, 5)

        res = solver.solve("Guess a number in the range of 1-5")
        answers = set(c["answer"] for c in res)
        assert answers == {"1", "2", "3", "4", "5"}


# ── Trivia Solver Tests ──────────────────────────────────────────────────────
class TestTriviaSolver:
    def test_exact_lookup(self):
        solver = TriviaSolver()
        q = "What is the capital of Minecraft?"
        a = "Mojang"
        solver.learn_answer(q, a)

        res = solver.solve(q)
        assert len(res) >= 1
        assert res[0]["answer"].lower() == a.lower()

    def test_skip_duplicate_learning(self):
        import time
        solver = TriviaSolver()
        q = f"Which unique mob test {time.time()} explodes?"
        a = "Creeper"
        assert solver.learn_answer(q, a) is True
        # Learning identical answer again must return False to avoid re-learning
        assert solver.learn_answer(q, a) is False


# ── Solver Router Tests ──────────────────────────────────────────────────────
class TestSolverRouter:
    def test_type_detection(self, solver_router):
        assert solver_router.detect_type("fill the gaps", "c_w") == "fill"
        assert solver_router.detect_type("unscramble", "p a l p e") == "scramble"
        assert solver_router.detect_type("reverse", "redne") == "reverse"
        assert solver_router.detect_type("solve equation", "15 + 25") == "math"
        assert solver_router.detect_type("type letters", "hello") == "type_letters"
        assert solver_router.detect_type("guess number", "1-50") == "guess_number"
        assert solver_router.detect_type("answer the following", "What is...") == "trivia"

    def test_heuristic_fallback_detection(self, solver_router):
        assert solver_router.detect_type("", "c_w") == "fill"
        assert solver_router.detect_type("", "10 + 20") == "math"
        assert solver_router.detect_type("", "range of 1-100") == "guess_number"

    def test_full_solve_pipeline(self, solver_router):
        res = solver_router.solve("math", "12 * 12")
        assert len(res) >= 1
        assert res[0]["answer"] == "144"
        assert res[0]["solver"] == "MathSolver"
        assert res[0]["detected_type"] == "math"
