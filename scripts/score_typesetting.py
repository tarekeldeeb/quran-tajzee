#!/usr/bin/env python3
"""Typesetting score of every aya: natural single-line width in the DigitalKhatt font.

Source of truth: tarekeldeeb/quran-nazm, which sets the 1441H Madina text from
quran-madina-html v2 in the patched DigitalKhatt "QMH New Madina" font with HarfBuzz.
Its `Text` class is used as is, so widths match what Quran-Nazm's line breaker sees:

  * each word is shaped on its own, unstretched (no kashida, no shrink features);
  * words are joined by one normal space; the ayah-number marker is glued to the
    word before it with a 1.5x space (quran-madina-html's AYA_SPACE);
  * a phrase set as one line = its ayat side by side, one normal space between ayat.

Widths are given in em (font units / units-per-em) and in pixels at --px (default
24 px, the size of quran-madina-html's reference renders). Pixels scale linearly with
the font size, so the choice of size does not affect any comparison.

The basmala is a surah header line in the Mushaf, not part of aya 1; its width is
written once to data/scores/basmala_typesetting.tsv.

Output: data/scores/typesetting_ayat.tsv

    QURAN_NAZM=../quran-nazm QMH=../quran-madina-html python scripts/score_typesetting.py
"""

import argparse
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tajzee import DATA, quran  # noqa: E402

COLUMNS = ["sura", "aya", "words", "em", "px"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--nazm", default=os.environ.get("QURAN_NAZM", ROOT.parent / "quran-nazm"))
    ap.add_argument("--px", type=float, default=24.0, help="font size in pixels for the px column")
    ap.add_argument("--out", default=DATA / "scores" / "typesetting_ayat.tsv")
    args = ap.parse_args()

    # quran-nazm reads QMH (quran-madina-html v2 checkout) and NAZM_WORK (fonts from
    # its scripts/00_prepare.py) from the environment; see its docs/RENDERING.md.
    sys.path.insert(0, str(Path(args.nazm) / "scripts"))
    import render_mushaf as nazm  # noqa: E402

    text = nazm.Text()
    upem = text.font.face.upem
    to_em = 1.0 / upem

    q = quran.load()
    assert text.flat == [(a.sura, a.aya) for a in q.ayat], "aya numbering differs from Tanzil"

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(COLUMNS)
        for s, a in text.flat:
            units = text.units(s, a)
            width = sum(u_w for _, u_w in units) + text.sp * (len(units) - 1)
            words = sum(1 for tk in text.suras[s - 1]["ayas"][a - 1].split() if not tk.startswith(nazm.MARK))
            em = width * to_em
            w.writerow([s, a, words, f"{em:.4f}", f"{em * args.px:.1f}"])

    words = text.basmala.split()
    width = sum(text.width(t) for t in words) + text.sp * (len(words) - 1)
    with open(out.parent / "basmala_typesetting.tsv", "w", encoding="utf-8", newline="") as fh:
        fh.write("words\tem\tpx\n")
        fh.write(f"{len(words)}\t{width * to_em:.4f}\t{width * to_em * args.px:.1f}\n")

    with open(out.parent / "typesetting_constants.tsv", "w", encoding="utf-8", newline="") as fh:
        fh.write("name\tem\tpx\n")
        fh.write(f"space\t{text.sp * to_em:.4f}\t{text.sp * to_em * args.px:.2f}\n")
        fh.write(f"font_px\t\t{args.px:g}\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
