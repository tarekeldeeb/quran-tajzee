import itertools
import random
import unittest

from tajzee import juz
from tajzee.juz import Unit


def toy(sizes):
    return [Unit(1, i + 1, i + 1, "t", 1, 1, float(r), float(p)) for i, (r, p) in enumerate(sizes)]


def brute(us, parts, weight):
    """Exhaustive search for the least-squares division (small inputs only)."""
    c = juz.combined(us, weight)
    T = sum(c) / parts
    best = None
    for cuts in itertools.combinations(range(1, len(us)), parts - 1):
        b = (0,) + cuts + (len(us),)
        sums = [sum(c[x:y]) for x, y in zip(b, b[1:])]
        key = (max(abs(s - T) for s in sums), sum((s - T) ** 2 for s in sums))
        if best is None or key < best[0]:
            best = (key, list(cuts))
    return best


class SolverTest(unittest.TestCase):
    def test_matches_brute_force(self):
        rnd = random.Random(7)
        for _ in range(25):
            us = toy([(rnd.randint(1, 40), rnd.randint(1, 40)) for _ in range(11)])
            for parts in (2, 3, 4):
                sol = juz.solve(us, 0.5, parts=parts)
                (dstar, ssq), _ = brute(us, parts, 0.5)
                self.assertAlmostEqual(sol.max_dev, dstar, places=12)
                self.assertAlmostEqual(sol.sum_sq, ssq, places=12)

    def test_least_squares_tie_break(self):
        us = toy([(5, 5)] * 6)
        sol = juz.solve(us, 0.5, parts=3)
        self.assertEqual(sol.cuts, [2, 4])
        self.assertAlmostEqual(sol.max_dev, 0.0)

    def test_weight_extremes(self):
        us = toy([(10, 1), (1, 10), (10, 1), (1, 10)])
        self.assertEqual(juz.solve(us, 1.0, parts=2).cuts, [2])
        self.assertEqual(juz.solve(us, 0.0, parts=2).cuts, [2])


class RealDivisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.us = juz.units()
        cls.sol = juz.solve(cls.us, 0.5)

    def test_thirty_parts_cover_everything(self):
        self.assertEqual(len(self.sol.parts), 30)
        self.assertEqual(sum(len(p) for p in self.sol.parts), len(self.us))
        self.assertEqual((self.sol.parts[0][0].sura, self.sol.parts[0][0].first), (1, 1))
        self.assertEqual((self.sol.parts[-1][-1].sura, self.sol.parts[-1][-1].last), (114, 6))

    def test_balanced(self):
        self.assertLess(self.sol.max_dev * 30, 0.03)  # every juz within 3% of the target

    def test_surah_opening_costs(self):
        from tajzee import phrases, scores
        k = scores.constants()
        ps = {(p.sura, p.first): p for p in phrases.load()}
        u = next(x for x in self.us if (x.sura, x.first) == (2, 1))
        self.assertEqual(u.recitation, scores.score_phrase(ps[(2, 1)]).recitation + k.basmala_recitation)
        t9 = next(x for x in self.us if (x.sura, x.first) == (9, 1))
        self.assertEqual(t9.recitation, scores.score_phrase(ps[(9, 1)]).recitation)  # no basmala
        full = next(x for x in juz.units(header_weight=1.0) if (x.sura, x.first) == (2, 1))
        self.assertAlmostEqual(full.typeset_px - u.typeset_px, 2 * juz.LINE_EM * k.font_px, places=6)


if __name__ == "__main__":
    unittest.main()
