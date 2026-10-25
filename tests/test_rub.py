import itertools
import random
import unittest

from tajzee import rub, scores
from tajzee.rub import Aya

INF = float("inf")


def toy(n, rnd, phrase_every=3):
    # surah 0: no real surah, so neither the opening-ayat rule nor the counting data apply
    return [Aya(i, 0, i + 1, float(rnd.randint(1, 30)), float(rnd.randint(1, 30)),
                i % phrase_every == 0, "t") for i in range(n)]


def brute_cut(us, c, a, e, parts, pen_for, cap):
    """Exhaustive cut of ayat a..e-1 into `parts` (small inputs only)."""
    T = sum(c[a:e]) / parts
    best = None
    for cuts in itertools.combinations(range(a + 1, e), parts - 1):
        bb = (a,) + cuts + (e,)
        s = [sum(c[x:y]) for x, y in zip(bb, bb[1:])]
        if cap is not None and any(abs(x - T) > cap * T for x in s):
            continue
        cost = sum(((x - T) / T) ** 2 for x in s)
        for k, x in enumerate(cuts, start=2):
            if not us[x].phrase_start:
                p = pen_for(k)
                cost += INF if p == INF else p * p
        if best is None or cost < best[0] - 1e-15:
            best = (cost, [a] + list(cuts))
    return best


def brute(us, juz_starts, m, hm, cap):
    """Exhaustive search of the joint method, one juz at a time (small inputs only)."""
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
                d = rub.solve(us, 0.5, m, hm, cap, juz_starts=js, method="joint",
                              objective="penalized", head_ayat=0)
                self.assertEqual(d.starts, [0] + want[0][1] + [11] + want[1][1])

    def test_nested_matches_brute_force(self):
        rnd = random.Random(9)
        for _ in range(6):
            us = toy(30, rnd)
            js = [0, 14]
            c = rub.mix(us)
            for m, hm, cap in ((0.1, INF, None), (0.0, 0.05, None), (0.2, INF, 0.8)):
                hizb = []
                for a, e in zip(js, js[1:] + [len(us)]):
                    hizb += brute_cut(us, c, a, e, 2, lambda k: hm, None)[1]
                want, ok = [], True
                for a, e in zip(hizb, hizb[1:] + [len(us)]):
                    r = brute_cut(us, c, a, e, 4, lambda k: m, cap)
                    if r is None or r[0] == INF:
                        ok = False
                        break
                    want += r[1]
                if not ok:
                    continue
                self.assertEqual(rub.solve(us, 0.5, m, hm, cap, juz_starts=js, objective="penalized",
                                           head_ayat=0).starts, want)

    def test_phrase_only_matches_brute_force(self):
        def best(us, c, a, e, parts):
            T = sum(c[a:e]) / parts
            top = None
            for cuts in itertools.combinations([i for i in range(a + 1, e) if us[i].phrase_start], parts - 1):
                bb = (a,) + cuts + (e,)
                s = [sum(c[x:y]) for x, y in zip(bb, bb[1:])]
                key = (round(max(abs(x - T) for x in s), 12), sum((x - T) ** 2 for x in s))
                if top is None or key < top[0]:
                    top = (key, [a] + list(cuts))
            return top[1]

        rnd = random.Random(13)
        for _ in range(8):
            us = toy(36, rnd, phrase_every=2)
            js = [0, 18]
            c = rub.mix(us)
            hizb = []
            for a, e in zip(js, js[1:] + [len(us)]):
                hizb += best(us, c, a, e, 2)
            want = []
            for a, e in zip(hizb, hizb[1:] + [len(us)]):
                want += best(us, c, a, e, 4)
            got = rub.solve(us, juz_starts=js, head_ayat=0, objective="minimax+lsq").starts
            self.assertEqual(got, want)


class WaqfObjectiveTest(unittest.TestCase):
    def test_matches_brute_force(self):
        # toy surah 0 has no grades: every start costs the ungraded points, except aya 1 (a surah end)
        from tajzee import waqf
        rnd = random.Random(11)
        wp, wr, wt = rub.SHARES
        for _ in range(5):
            us = toy(20, rnd, phrase_every=1)
            js = [0, 10]

            def cost(a, b, cuts):
                bs = [a] + list(cuts) + [b]
                R = [sum(u.recitation for u in us[x:y]) for x, y in zip(bs, bs[1:])]
                P = [sum(u.typeset_px for u in us[x:y]) for x, y in zip(bs, bs[1:])]
                tr, tp = sum(R) / len(R), sum(P) / len(P)
                return (sum(wr * ((r - tr) / tr) ** 2 for r in R) + sum(wt * ((x - tp) / tp) ** 2 for x in P)
                        + sum(wp * (rub.POINT_VALUE * waqf.points(us, j)) ** 2 for j in cuts))

            def best(a, b, parts):
                cand = [i for i in range(a + 1, b) if us[i].phrase_start]
                return min(itertools.combinations(cand, parts - 1), key=lambda cs: cost(a, b, cs))

            c = rub.mix(us)
            hz = []
            for a, b in zip(js, js[1:] + [20]):        # hizb: unchanged rule (minimax + least squares)
                hz += rub._cut_phrases(us, c, a, b, 2, 0)
            want = []
            for a, b in zip(hz, hz[1:] + [20]):
                want += [a, *best(a, b, 4)]
            self.assertEqual(rub.solve(us, juz_starts=js, head_ayat=0).starts, want)

    def test_pause_points(self):
        from tajzee import waqf
        us = rub.ayat()
        at = {u.ref: u.index for u in us}
        self.assertEqual(waqf.points(us, at["3:1"]), 1)     # surah end
        self.assertEqual(waqf.points(us, at["2:26"]), 2)    # 2:25 خالدون: تام
        self.assertEqual(waqf.points(us, at["26:116"]), 5)  # 26:115: جائز
        self.assertEqual(waqf.PAUSE_POINTS["ليس بوقف"], 9)


class HeadRuleTest(unittest.TestCase):
    def test_head_rule_respected_and_optimal(self):
        # 15 ayat of surahs 2 and 3; every aya a phrase start; aya 2..7 forbidden
        rnd = random.Random(3)
        us = [Aya(i, 2 + i // 15, i % 15 + 1, float(rnd.randint(1, 30)), float(rnd.randint(1, 30)), True, "t")
              for i in range(30)]
        c = rub.mix(us)
        ok = [i for i in range(1, 30) if not (2 <= us[i].aya <= 7) and not rub.disputed_end(us[i])]
        T = sum(c) / 8
        best = None
        for cuts in itertools.combinations(ok, 7):
            bb = (0,) + cuts + (30,)
            s = [sum(c[x:y]) for x, y in zip(bb, bb[1:])]
            key = (round(max(abs(x - T) for x in s), 12), sum((x - T) ** 2 for x in s))
            if best is None or key < best[0]:
                best = (key, [0] + list(cuts))
        got = rub.solve(us, juz_starts=[0], method="joint", objective="minimax+lsq").starts
        self.assertEqual(got, best[1])


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

    def test_every_boundary_opens_a_phrase(self):
        jset = set(self.d.juz_starts)
        self.assertEqual(self.d.mid_phrase, [])
        self.assertTrue(all(self.us[s].phrase_start for s in self.d.starts if s not in jset))

    def test_no_rub_at_ayat_2_to_7(self):
        short = next(u for u in self.us if u.sura == 67 and u.aya == 5)
        self.assertTrue(rub.in_head(short))  # the rule holds in short surahs too (Al-Mulk, juz 29)
        exempt = next(u for u in self.us if u.sura == 61 and u.aya == 5)
        self.assertFalse(rub.in_head(exempt))  # juz 28 is exempt
        jset = set(self.d.juz_starts)
        for d in (self.d, rub.solve(self.us, objective="penalized", cap=None)):
            bad = [self.us[i].ref for i in d.starts if i not in jset and rub.in_head(self.us[i])]
            self.assertEqual(bad, [])

    def test_every_boundary_is_an_agreed_aya_end(self):
        self.assertEqual(rub.disputed_end(next(u for u in self.us if u.ref == "20:42")),
                         ["basri", "madani-first", "madani-last", "makki"])  # «لنفسي» 20:41: Kufi and Shami only
        self.assertEqual([self.us[i].ref for i in self.d.starts if rub.disputed_end(self.us[i])], [])
        trad = scores.traditional_starts(1)
        self.assertEqual([self.us[i].ref for i in trad if rub.disputed_end(self.us[i])], [])

    def test_penalized_phrase_starts_only(self):
        d = rub.solve(self.us, mid_phrase=INF, cap=None, objective="penalized")
        self.assertEqual(d.mid_phrase, [])


if __name__ == "__main__":
    unittest.main()
