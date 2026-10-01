import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from solver.fill_solver import FillSolver


class TestFillSolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solver = FillSolver()

    def test_known_samples(self):
        cases = [
            ("Ne_h_r Br_c_ _la_", "Nether Brick Slab"),
            ("Ac_ci_ Pl_nks", "Acacia Planks"),
            ("D_am_nd Bl_ck", "Diamond Block"),
            ("O_k Pl_nks", "Oak Planks"),
            ("__elot Sp_wn ___", "Ocelot Spawn Egg"),
            ("Inf_s_e_ _eeps_a__", "Infested Deepslate"),
            ("D__d Hor_ __r_l __ll F_n", "Dead Horn Coral Wall Fan"),
            ("Wh_te Car___", "White Carpet"),
            ("L_m_ _hul_er _o_", "Lime Shulker Box"),
            ("Zom_ie __rs_", "Zombie Horse"),
            ("_an_ro_e St___s", "Mangrove Stairs"),
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