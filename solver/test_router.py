import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from solver.router import SolverRouter


class TestSolverRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.router = SolverRouter()

    def test_routing_fill_gaps(self):
        results = self.router.solve("Fill the gaps:", "Ne_h_r Br_c_ _la_")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["answer"], "Nether Brick Slab")
        self.assertEqual(results[0]["solver"], "FillSolver")

    def test_routing_unscramble(self):
        results = self.router.solve("Unscramble the letters:", "hticW")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["answer"], "Witch")
        self.assertEqual(results[0]["solver"], "ScrambleSolver")

    def test_routing_reverse(self):
        results = self.router.solve("Unreverse the letters:", "roodparT aicacA")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["answer"], "Acacia Trapdoor")
        self.assertEqual(results[0]["solver"], "ReverseSolver")

    def test_routing_math(self):
        results = self.router.solve("Solve the equation:", "-10 * -2 - (-2) + 0")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["answer"], "22")
        self.assertEqual(results[0]["solver"], "MathSolver")

    def test_routing_type_letters(self):
        results = self.router.solve("Type the letters:", "Jack o'Lantern")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["answer"], "Jack o'Lantern")
        self.assertEqual(results[0]["solver"], "TypeLetters")

    def test_routing_guess_number(self):
        results = self.router.solve("Guess the number:", "It is within the range of 1-15")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["solver"], "NumberSolver")
        val = int(results[0]["answer"])
        self.assertTrue(1 <= val <= 15)

    def test_routing_trivia(self):
        results = self.router.solve("Answer the following:", "What level is the build limit in the overworld?")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["answer"], "320")
        self.assertEqual(results[0]["solver"], "TriviaSolver")


if __name__ == "__main__":
    unittest.main()
