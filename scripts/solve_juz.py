#!/usr/bin/env python3
"""Solve the 30 balanced juz and write data/juz/juz.tsv.

    python scripts/solve_juz.py [--weight 0.5] [--objective minimax+lsq]

weight is the recitation share of the combined score (0.5 = 50/50 with typesetting).
See tajzee/juz.py for the model and the exact dynamic program.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tajzee import DATA, juz, quran  # noqa: E402

COLUMNS = ["juz", "start", "end", "phrases", "ayat", "words", "recitation", "typeset_px",
           "recitation_dev_pct", "typeset_dev_pct", "combined_dev_pct", "first_topic"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--weight", type=float, default=0.5)
    ap.add_argument("--objective", default="penalized",
                    choices=["penalized", "minimax+lsq", "minimax", "lsq", "each"])
    ap.add_argument("--break-penalty", type=float, default=juz.BREAK_PENALTY,
                    help="penalized objective: a juz starting mid-surah costs like a juz this far off (fraction)")
    ap.add_argument("--cap", type=float, default=juz.CAP,
                    help="penalized objective: every juz within this fraction of the target")
    ap.add_argument("--header-weight", type=float, default=juz.HEADER_WEIGHT,
                    help="printed surah header lines in the typesetting size (0 = text only)")
    ap.add_argument("--out", default=DATA / "juz" / "juz.tsv")
    args = ap.parse_args()

    us = juz.units(header_weight=args.header_weight)
    if args.objective == "penalized":
        sol = juz.solve(us, args.weight, break_penalty=args.break_penalty, cap=args.cap)
    else:
        sol = juz.solve(us, args.weight, objective=args.objective)
    R = sum(u.recitation for u in us) / juz.PARTS
    P = sum(u.typeset_px for u in us) / juz.PARTS

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(COLUMNS)
        for n, part in enumerate(sol.parts, 1):
            rec = sum(u.recitation for u in part)
            px = sum(u.typeset_px for u in part)
            dr, dp = rec / R - 1, px / P - 1
            dc = args.weight * dr + (1 - args.weight) * dp
            row = [n, f"{part[0].sura}:{part[0].first}", f"{part[-1].sura}:{part[-1].last}", len(part),
                   sum(u.ayat for u in part), sum(u.words for u in part), int(round(rec)), f"{px:.1f}",
                   f"{dr * 100:+.2f}", f"{dp * 100:+.2f}", f"{dc * 100:+.2f}", part[0].topic]
            w.writerow(row)
            rows.append(row)
    meta = dict(weight=args.weight, objective=args.objective, header_weight=args.header_weight, parts=juz.PARTS,
                break_penalty=args.break_penalty if args.objective == "penalized" else 0.0,
                cap=args.cap if args.objective == "penalized" else None, surah_breaks=sol.surah_breaks,
                max_combined_dev_pct=sol.max_dev * juz.PARTS * 100,
                starts=[r[1] for r in rows])
    (out.parent / "solution.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {out}: worst combined deviation {meta['max_combined_dev_pct']:.2f}% of a juz, "
          f"{sol.surah_breaks} juz start mid-surah")
    for r in rows:
        s, a = map(int, r[1].split(":"))
        print(f"{r[0]:>2}  {r[1]:>7} {quran.SURAH_NAMES[s]:<10} {r[10]:>7}%  {r[11]}")


if __name__ == "__main__":
    main()
