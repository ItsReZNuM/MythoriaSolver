import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from solver.scramble_solver import ScrambleSolver


class TestScrambleSolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solver = ScrambleSolver()

    def test_known_samples(self):
        cases = [
            ("hticW", "Witch"),
            ("maooBb oiMcsa aSsitr", "Bamboo Mosaic Stairs"),
            ("zutQra itaSsr", "Quartz Stairs"),
            ("blalSnow", "Snowball"),
            ("rTeppad etsCh", "Trapped Chest"),
            ("hriBc taBo ihwt stheC", "Birch Boat with Chest"),
            ("iSmtghni eamltpeT", "Smithing Template"),
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


if __name__ == "__main__":
    unittest.main()
