import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from solver.math_solver import MathSolver


class TestMathSolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solver = MathSolver()

    def test_known_samples(self):
        cases = [
            ("-10 * -2 - (-2) + 0", "22"),
            ("4 * 8 * 3 - 8", "88"),
            ("-4 - (-6) + (-9) - (-1)", "-6"),
            ("2 + 0 * 5 - 2", "0"),
            ("100 / 4", "25"),
            ("15 + 3 * 2", "21"),
        ]

        for question, expected in cases:
            with self.subTest(question=question, expected=expected):
                results = self.solver.solve(question)
                self.assertTrue(len(results) > 0, f"No answer found for {question}")
                best_answer = results[0]["answer"]
                self.assertEqual(
                    best_answer,
                    expected,
                    f"Expected '{expected}' for '{question}', got '{best_answer}'",
                )

    def test_security_rejections(self):
        dangerous_inputs = [
            "__import__('os').system('calc')",
            "open('test.txt')",
            "exec('a = 1')",
            "eval('2+2')",
            "x = 5",
        ]
        for bad in dangerous_inputs:
            with self.subTest(bad=bad):
                results = self.solver.solve(bad)
                self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
