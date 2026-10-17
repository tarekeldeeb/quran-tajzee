#!/usr/bin/env python3
"""Sum the per-aya scores into data/scores/phrases.tsv, one row per phrase.

    python scripts/score_phrases.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tajzee import phrases, scores  # noqa: E402

COLUMNS = ["sura", "from", "to", "ayat", "words", "letters", "recitation", "typeset_em", "typeset_px"]


def main() -> None:
    out = scores.SCORES / "phrases.tsv"
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(COLUMNS)
        for p in phrases.load():
            s = scores.score_phrase(p)
            w.writerow([p.sura, p.first, p.last, s.ayat, s.words, s.letters, s.recitation,
                        f"{s.typeset_em:.4f}", f"{s.typeset_px:.1f}"])
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
