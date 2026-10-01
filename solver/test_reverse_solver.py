import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from solver.reverse_solver import ReverseSolver


class TestReverseSolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solver = ReverseSolver()

    def test_known_samples(self):
        cases = [
            ("roodparT aicacA", "Acacia Trapdoor"),
            ("attocarreT dezalG kniP", "Pink Glazed Terracotta"),
            ("sriatS enotskcalB dehsiloP", "Polished Blackstone Stairs"),
            ("metS noleM dehcattA", "Attached Melon Stem"),
            ("woC", "Cow"),
            ("SWGihXI", "IXhiGWS"),
            ("MqJwqQH", "HQqwJqM"),
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
