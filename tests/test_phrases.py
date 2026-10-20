import unittest
from pathlib import Path

from tajzee import ROOT, phrases, quran, reviews
from tajzee.phrases import Phrase

class SourceTextTest(unittest.TestCase):
    def test_tanzil_shape(self):
        q = quran.load()
        self.assertEqual(len(q), 6236)
        self.assertEqual(len(q.counts), 114)
        self.assertEqual(q.counts[2], 286)
        self.assertEqual(q.counts[108], 3)


class PhraseListTest(unittest.TestCase):
    def test_canonical_list_is_valid(self):
        rep = phrases.validate(phrases.load(), quran.load())
        self.assertTrue(rep.ok, "\n".join(rep.errors[:20]))

    def test_round_trip(self):
        ps = phrases.load()
        tmp = ROOT / "build" / "roundtrip.tsv"
        tmp.parent.mkdir(exist_ok=True)
        phrases.save(ps, tmp)
        self.assertEqual(phrases.load(tmp), ps)

    def test_validation_catches_problems(self):
        q = quran.load()
        bad = [Phrase(108, 1, 2, "x"), Phrase(108, 2, 3, "y")]  # overlap on 108:2
        rep = phrases.validate(bad, q, full=False)
        self.assertIn("108:2: covered by 2 phrases", rep.errors)
        self.assertTrue(any("ayat (max" in e for e in phrases.validate([Phrase(2, 1, 11, "t")], q, full=False).errors))


class ReviewsTest(unittest.TestCase):
    def test_merge_marks_chain(self):
        ps = [Phrase(1, 1, 1, "البسملة"), Phrase(1, 2, 4, "الحمد"), Phrase(1, 5, 5, "العبادة"),
              Phrase(1, 6, 7, "الهداية")]
        marks = {"1:1-1": {"status": "merge"}, "1:2-4": {"status": "merge"}, "1:5-5": {"status": "merge"}}
        res = reviews.apply(ps, marks)
        self.assertEqual([p.id for p in res.phrases], ["1:1-7"])
        self.assertFalse(res.stale)
        self.assertTrue(phrases.validate(res.phrases, quran.load(), full=False).ok)

    def test_split_and_topic(self):
        ps = [Phrase(108, 1, 3, "الكوثر")]
        res = reviews.apply(ps, {"108:1-3": {"status": "split", "splitAfter": 1}})
        self.assertEqual([p.id for p in res.phrases], ["108:1-1", "108:2-3"])
        res = reviews.apply(ps, {"108:1-3": {"status": "topic", "topic": "نعمة الكوثر"}})
        self.assertEqual(res.phrases[0].topic, "نعمة الكوثر")

    def test_stale_marks_are_reported(self):
        res = reviews.apply([Phrase(108, 1, 3, "x")], {"108:1-2": {"status": "ok"}})
        self.assertEqual(res.stale, ["108:1-2"])


if __name__ == "__main__":
    unittest.main()
