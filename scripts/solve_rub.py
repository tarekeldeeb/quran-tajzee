#!/usr/bin/env python3
"""Cut the traditional juz into balanced hizb and rub' (Task 4).

    python scripts/solve_rub.py [--mid-phrase 0.10] [--hizb-mid-phrase inf] [--cap 0.10]

Writes data/rub/rub.tsv (240 rub'), data/rub/solution.json and data/rub/phrase-splits.tsv
(the phrases a juz or rub' start falls inside: proposals for the next phrase review).
See tajzee/rub.py for the model.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tajzee import DATA, phrases, rub  # noqa: E402

COLUMNS = ["rub", "juz", "hizb", "quarter", "start", "end", "ayat", "recitation", "typeset_px",
           "recitation_dev_pct", "typeset_dev_pct", "combined_dev_pct", "at_phrase", "traditional_start",
           "first_topic"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--weight", type=float, default=0.5)
    ap.add_argument("--mid-phrase", type=float, default=rub.MID_PHRASE,
                    help="a rub' starting inside a phrase costs like a rub' this far off (fraction; inf = never)")
    ap.add_argument("--hizb-mid-phrase", type=float, default=rub.HIZB_MID_PHRASE,
                    help="the same for a hizb start (default inf: a hizb always opens a phrase)")
    ap.add_argument("--cap", type=float, default=rub.CAP, help="every rub' within this fraction of 1/8 of its juz")
    ap.add_argument("--out", default=DATA / "rub" / "rub.tsv")
    args = ap.parse_args()

    us = rub.ayat()
    d = rub.solve(us, args.weight, args.mid_phrase, args.hizb_mid_phrase, args.cap)
    rec = rub.relative(us, d.starts, [u.recitation for u in us], 8)
    px = rub.relative(us, d.starts, [u.typeset_px for u in us], 8)
    mixv = rub.relative(us, d.starts, rub.mix(us, args.weight), 8)
    rs = rub.sizes(us, d.starts, [u.recitation for u in us])
    ps = rub.sizes(us, d.starts, [u.typeset_px for u in us])
    trad = set(rub.scores.traditional_starts(1))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    bounds = d.starts + [len(us)]
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(COLUMNS)
        for n, (a, b) in enumerate(zip(bounds, bounds[1:])):
            w.writerow([n + 1, n // 8 + 1, n // 4 + 1, n % 4 + 1, us[a].ref, us[b - 1].ref, b - a,
                        int(round(rs[n])), f"{ps[n]:.1f}", f"{rec[n] * 100:+.2f}", f"{px[n] * 100:+.2f}",
                        f"{mixv[n] * 100:+.2f}", int(us[a].phrase_start), int(a in trad), us[a].topic])

    # phrases cut by a juz start (traditional, fixed) or by a rub' start (solver)
    by_aya = {}
    for p in phrases.load():
        for x in range(p.first, p.last + 1):
            by_aya[(p.sura, x)] = p
    juz_set = set(d.juz_starts)
    with open(out.parent / "phrase-splits.tsv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["sura", "from", "to", "split_after", "reason", "topic"])
        for i in sorted(set(d.mid_phrase) | {j for j in d.juz_starts if not us[j].phrase_start}):
            p = by_aya[(us[i].sura, us[i].aya)]
            w.writerow([p.sura, p.first, p.last, us[i].aya - 1, "juz" if i in juz_set else "rub", p.topic])

    worst = max(abs(x) for x in mixv)
    hz = rub.relative(us, d.hizb_starts(), rub.mix(us, args.weight), 2)
    meta = dict(weight=args.weight, mid_phrase=args.mid_phrase, hizb_mid_phrase=args.hizb_mid_phrase,
                cap=args.cap, max_rub_dev_pct=round(worst * 100, 2),
                max_hizb_dev_pct=round(max(abs(x) for x in hz) * 100, 2),
                rub_inside_phrase=len(d.mid_phrase), same_as_traditional=sum(1 for s in d.starts if s in trad),
                starts=[us[s].ref for s in d.starts])
    (out.parent / "solution.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {out}: worst rub' {meta['max_rub_dev_pct']}% of its target, worst hizb "
          f"{meta['max_hizb_dev_pct']}%, {len(d.mid_phrase)} rub' start inside a phrase, "
          f"{meta['same_as_traditional']} of 240 starts as traditional")


if __name__ == "__main__":
    main()
