import itertools
import random
import unittest

from tajzee import rub, scores
from tajzee.rub import Aya

INF = float("inf")


def toy(n, rnd, phrase_every=3):
    return [Aya(i, 1, i + 1, float(rnd.randint(1, 30)), float(rnd.randint(1, 30)),
                i % phrase_every == 0, "t") for i in range(n)]


def brute(us, juz_starts, m, hm, cap):
    """Exhaustive search, one juz at a time (small inputs only)."""
    c = rub.mix(us)
    b = juz_starts + [len(us)]
    best_all = []
    for a, e in zip(b, b[1:]):
        T = sum(c[a:e]) / 8
        best = None
        for cuts in itertools.combinations(range(a + 1, e), 7):
            bb = (a,) + cuts + (e,)
            s = [sum(c[x:y]) for x, y in zip(bb, bb[1:])]
            if cap is not None and any(abs(x - T) > cap * T for x in s):
                continue
            cost = sum(((x - T) / T) ** 2 for x in s)
            for k, x in enumerate(cuts, start=2):
                if not us[x].phrase_start:
                    p = hm if k == rub.HIZB_PART else m
                    cost += INF if p == INF else p * p
            if best is None or cost < best[0] - 1e-15:
                best = (cost, list(cuts))
        best_all.append(best)
    return best_all


class RubSolverTest(unittest.TestCase):
    def test_matches_brute_force(self):
        rnd = random.Random(5)
        for _ in range(6):
            us = toy(22, rnd)
            js = [0, 11]
            for m, hm, cap in ((0.1, INF, None), (0.0, 0.0, None), (0.2, INF, 0.8)):
                want = brute(us, js, m, hm, cap)
                if any(x is None or x[0] == INF for x in want):
                    continue
                d = rub.solve(us, 0.5, m, hm, cap, juz_starts=js)
                self.assertEqual(d.starts, [0] + want[0][1] + [11] + want[1][1])


class RealDivisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.us = rub.ayat()
        cls.d = rub.solve(cls.us)

    def test_shape(self):
        self.assertEqual(len(self.d.starts), 240)
        self.assertEqual(self.d.starts, sorted(set(self.d.starts)))
        self.assertEqual(self.d.starts[::8], scores.traditional_starts(8))  # juz unchanged

    def test_hizb_open_phrases(self):
        for h, s in enumerate(self.d.hizb_starts()):
            if h % 2:  # the second hizb of each juz; the first is the fixed juz start
                self.assertTrue(self.us[s].phrase_start, self.us[s].ref)

    def test_within_cap(self):
        rel = rub.relative(self.us, self.d.starts, rub.mix(self.us), 8)
        self.assertLessEqual(max(abs(x) for x in rel), rub.CAP + 1e-12)

    def test_phrase_starts_only(self):
        d = rub.solve(self.us, mid_phrase=INF, cap=None)
        self.assertEqual(d.mid_phrase, [])


if __name__ == "__main__":
    unittest.main()
