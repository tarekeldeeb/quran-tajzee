import unittest

from tajzee import phrases, quran, scores
from tajzee.phrases import Phrase


class AyaScoresTest(unittest.TestCase):
    def test_every_aya_scored(self):
        a = scores.ayat()
        self.assertEqual(len(a), 6236)
        self.assertEqual(set(a), {(x.sura, x.aya) for x in quran.load().ayat})
        self.assertTrue(all(x.recitation > 0 and x.typeset_px > 0 for x in a.values()))

    def test_known_values(self):
        a = scores.ayat()
        # basmala of Al-Fatiha: 13 plain letters + madd 2 (ـٰ) + madd 'arid 4 at the stop
        self.assertEqual(a[(1, 1)].recitation, 19)
        # الم: alif plus two lazim madd of 6
        self.assertEqual(a[(2, 1)].recitation, 13)
        self.assertEqual(scores.constants().basmala_recitation, 19)
        self.assertEqual(sum(x.words for x in a.values()), 77433)


class RangeTest(unittest.TestCase):
    def test_phrase_is_sum_of_ayat_plus_spaces(self):
        a, k = scores.ayat(), scores.constants()
        s = scores.score_phrase(Phrase(108, 1, 3, "الكوثر"))
        self.assertEqual(s.recitation, sum(a[(108, n)].recitation for n in (1, 2, 3)))
        self.assertAlmostEqual(s.typeset_px, sum(a[(108, n)].typeset_px for n in (1, 2, 3)) + 2 * k.space_px,
                               places=1)

    def test_basmala_added_per_surah_opening(self):
        k = scores.constants()
        refs = [(108, 3), (109, 1)]
        plain = scores.score_range(refs)
        withb = scores.score_range(refs, with_basmala=True)
        self.assertEqual(withb.recitation - plain.recitation, k.basmala_recitation)
        self.assertEqual(scores.score_range([(9, 1)], with_basmala=True).recitation,
                         scores.score_range([(9, 1)]).recitation)

    def test_phrase_totals_match_aya_totals(self):
        total = sum(scores.score_phrase(p).recitation for p in phrases.load())
        self.assertEqual(total, sum(x.recitation for x in scores.ayat().values()))

    def test_traditional_juz(self):
        starts = scores.traditional_starts(8)
        self.assertEqual(len(starts), 30)
        flat = [(a.sura, a.aya) for a in quran.load().ayat]
        self.assertEqual(flat[starts[1]], (2, 142))
        self.assertEqual(flat[starts[29]], (78, 1))


if __name__ == "__main__":
    unittest.main()
