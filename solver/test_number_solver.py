import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from solver.number_solver import NumberSolver


class TestNumberSolver(unittest.TestCase):
    def test_random_guess_within_range(self):
        solver = NumberSolver(mode="random")
        question = "It is within the range of 1-15"
        for _ in range(20):
            results = solver.solve(question, limit=1)
            self.assertEqual(len(results), 1)
            val = int(results[0]["answer"])
            self.assertTrue(1 <= val <= 15)
            self.assertEqual(results[0]["type"], "random_guess")

        all_results = solver.solve(question)
        self.assertEqual(len(all_results), 15)

    def test_skip_mode(self):
        solver = NumberSolver(mode="skip")
        results = solver.solve("It is within the range of 1-15")
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
