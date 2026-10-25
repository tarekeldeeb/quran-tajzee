import unittest

from tajzee import rub, scores, waqf


class WaqfTest(unittest.TestCase):
    def test_grade_words_stand_alone(self):
        self.assertEqual(waqf.grade(" كاف، ومثله"), "كاف")
        self.assertEqual(waqf.grade(" بالكافرين تام"), "تام")       # not «كاف» inside الكافرين
        self.assertEqual(waqf.grade(" ليس بوقف؛ لأن"), "ليس بوقف")
        self.assertEqual(waqf.grade(" نام، ولا وقف إلى"), "تام")     # the edition's typo at 25:20
        self.assertIsNone(waqf.grade(" قرأ نافع بالياء"))

    def test_skeleton_matches_both_spellings(self):
        self.assertEqual(waqf.skeleton("الصلاة"), waqf.skeleton("ٱلصَّلَوٰةَ"))
        self.assertEqual(waqf.skeleton("الكتاب"), waqf.skeleton("ٱلْكِتَٰبُ"))

    def test_known_grades(self):
        s = waqf.stops()
        self.assertEqual(s[(2, 25)], {"muktafa": "تام", "manar": "تام"})   # Ghayth: «تام في أعلى درجاته»
        self.assertEqual(s[(26, 115)]["manar"], "جائز")
        self.assertGreater(len(s), 5000)

    def test_ghayth_quarters(self):
        qs = waqf.quarters()
        self.assertEqual([x.n for x in qs], list(range(1, 241)))
        self.assertEqual((qs[0].madina_end, qs[0].ghayth_end, qs[0].grade, qs[0].standing),
                         ("2:25", "2:25", "تام", "consensus"))
        self.assertEqual(qs[2].ghayth_end, "2:60")                     # «مفسدين … عند الأكثرين»
        self.assertGreater(sum(x.ghayth_end == x.madina_end for x in qs), 190)

    def test_boundaries_are_strong_stops(self):
        us = rub.ayat()
        for starts in (rub.solve(us).starts, scores.traditional_starts(1)):
            weak = [i for i in starts if i and us[i].aya != 1
                    and (waqf.best(us[i - 1].sura, us[i - 1].aya) or 0) < 3]
            self.assertLess(len(weak), 12)


if __name__ == "__main__":
    unittest.main()
