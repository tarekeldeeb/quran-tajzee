import itertools
import random
import unittest

from tajzee import juz
from tajzee.juz import Unit


def toy(sizes):
    return [Unit(1, i + 1, i + 1, "t", 1, 1, float(r), float(p)) for i, (r, p) in enumerate(sizes)]


def brute_penalized(us, parts, weight, p, cap=None, late=None):
    """Exhaustive search for the penalized objective (small inputs only).

    late = (N, p_late): the last N parts use p_late instead of p."""
    c = juz.combined(us, weight)
    T = sum(c) / parts
    best = None
    for cuts in itertools.combinations(range(1, len(us)), parts - 1):
        b = (0,) + cuts + (len(us),)
        sums = [sum(c[x:y]) for x, y in zip(b, b[1:])]
        if cap is not None and any(abs(s - T) > cap * T for s in sums):
            continue
        cost = sum(((s - T) / T) ** 2 for s in sums)
        for k, x in enumerate(cuts, start=2):  # cut x starts part k
            if us[x].first != 1:
                pk = late[1] if (late and k > parts - late[0]) else p
                cost += float("inf") if pk == float("inf") else pk * pk
        if best is None or cost < best[0] - 1e-15:
            best = (cost, list(cuts))
    return best


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

    def test_penalized_matches_brute_force(self):
        rnd = random.Random(11)
        for _ in range(25):
            # units in up to 4 surahs; a cut at a unit with first == 1 opens a surah
            us, sura, aya = [], 1, 1
            for _ in range(11):
                if rnd.random() < 0.3:
                    sura, aya = sura + 1, 1
                us.append(Unit(sura, aya, aya, "t", 1, 1, float(rnd.randint(1, 40)), float(rnd.randint(1, 40))))
                aya += 1
            for p, cap in ((0.05, None), (0.2, None), (0.2, 0.6)):
                want = brute_penalized(us, 3, 0.5, p, cap)
                if want is None:  # no division within the cap
                    continue
                sol = juz.solve(us, 0.5, parts=3, break_penalty=p, cap=cap)
                c = juz.combined(us, 0.5)
                T = sum(c) / 3
                got = sum(((sum(u_c for u_c in c[a:b]) - T) / T) ** 2
                          for a, b in zip([0] + sol.cuts, sol.cuts + [len(us)])) + p * p * sol.surah_breaks
                self.assertAlmostEqual(got, want[0], places=10)

    def test_late_penalty_matches_brute_force(self):
        rnd = random.Random(23)
        for _ in range(25):
            us, sura, aya = [], 1, 1
            for _ in range(12):
                if rnd.random() < 0.35:
                    sura, aya = sura + 1, 1
                us.append(Unit(sura, aya, aya, "t", 1, 1, float(rnd.randint(1, 40)), float(rnd.randint(1, 40))))
                aya += 1
            for p, pl, n in ((0.02, 0.3, 1), (0.0, float("inf"), 2), (0.1, 0.5, 2)):
                want = brute_penalized(us, 4, 0.5, p, None, (n, pl))
                if want is None or want[0] == float("inf"):
                    with self.assertRaises(ValueError):
                        juz.solve(us, 0.5, parts=4, break_penalty=p, late_penalty=pl, late_parts=n)
                    continue
                sol = juz.solve(us, 0.5, parts=4, break_penalty=p, late_penalty=pl, late_parts=n)
                self.assertEqual(sol.cuts, want[1])

    def test_penalty_moves_cut_to_surah_start(self):
        # the balanced cut (index 2) is mid-surah; surah 2 starts at index 3.
        # Moving the cut there costs 0.405 in squared relative deviation.
        us = [Unit(1, 1, 1, "t", 1, 1, 10, 10), Unit(1, 2, 2, "t", 1, 1, 10, 10),
              Unit(1, 3, 3, "t", 1, 1, 9, 9), Unit(2, 1, 1, "t", 1, 1, 11, 11)]
        self.assertEqual(juz.solve(us, 0.5, parts=2, objective="lsq").cuts, [2])
        self.assertEqual(juz.solve(us, 0.5, parts=2, break_penalty=0.5).cuts, [2])  # 0.25 < 0.405
        self.assertEqual(juz.solve(us, 0.5, parts=2, break_penalty=0.7).cuts, [3])  # 0.49 > 0.405

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
