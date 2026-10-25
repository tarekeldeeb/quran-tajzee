#!/usr/bin/env python3
"""Cut the traditional juz into balanced hizb and rub' (Task 4).

    python scripts/solve_rub.py [--method nested] [--objective minimax+lsq]
    python scripts/solve_rub.py --objective penalized [--mid-phrase 0.10] [--cap 0.10]

The default objective starts every hizb and rub' at a phrase start. Writes:

* data/rub/hizb.tsv: 60 hizb, deviation from 1/2 of their juz;
* data/rub/rub.tsv: 240 rub', deviation from 1/4 of their hizb;
* data/rub/solution.json;
* data/rub/phrase-pauses.tsv: every phrase with the pause category and points of its start;
* data/rub/phrase-splits.tsv: proposals for the next phrase review. These are the phrases a
  traditional juz start falls inside (reason juz), and the splits that would let the rub'
  balance better (reason balance, taken from the penalized objective).

See tajzee/rub.py for the model.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tajzee import DATA, phrases, rub, waqf  # noqa: E402

COLUMNS = ["start", "end", "ayat", "recitation", "typeset_px", "recitation_dev_pct", "typeset_dev_pct",
           "combined_dev_pct", "at_phrase", "at_surah", "traditional_start", "pause", "pause_points", "first_topic"]


def write_pauses(path, us):
    """Every phrase, with the pause category and points of the aya end before its start."""
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["start", "end", "pause", "pause_points", "muktafa", "manar", "topic"])
        starts = [u.index for u in us if u.phrase_start] + [len(us)]
        for a, b in zip(starts, starts[1:]):
            _, mk, mn = waqf.boundary(us, a) if a else ("", "", "")
            w.writerow([us[a].ref, us[b - 1].ref, waqf.category(us, a), waqf.points(us, a), mk, mn, us[a].topic])


def write(path, us, starts, group, trad, weight, rub_rows):
    """One row per unit; deviations against 1/group of the container (hizb or juz)."""
    rec = rub.relative(us, starts, [u.recitation for u in us], group)
    px = rub.relative(us, starts, [u.typeset_px for u in us], group)
    mixv = rub.relative(us, starts, rub.mix(us, weight), group)
    rs = rub.sizes(us, starts, [u.recitation for u in us])
    ps = rub.sizes(us, starts, [u.typeset_px for u in us])
    head = ["rub", "juz", "hizb", "quarter"] if rub_rows else ["hizb", "juz", "half"]
    bounds = list(starts) + [len(us)]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(head + COLUMNS)
        for n, (a, b) in enumerate(zip(bounds, bounds[1:])):
            ids = [n + 1, n // 8 + 1, n // 4 + 1, n % 4 + 1] if rub_rows else [n + 1, n // 2 + 1, n % 2 + 1]
            w.writerow(ids + [us[a].ref, us[b - 1].ref, b - a, int(round(rs[n])), f"{ps[n]:.1f}",
                              f"{rec[n] * 100:+.2f}", f"{px[n] * 100:+.2f}", f"{mixv[n] * 100:+.2f}",
                              int(us[a].phrase_start), int(us[a].aya == 1), int(a in trad),
                              waqf.category(us, a), waqf.points(us, a), us[a].topic])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--weight", type=float, default=0.5)
    ap.add_argument("--method", default=rub.METHOD, choices=["nested", "joint"],
                    help="nested: hizb first, then 4 rub' per hizb; joint: 8 rub' per juz at once")
    ap.add_argument("--objective", default=rub.OBJECTIVE, choices=["waqf", "minimax+lsq", "penalized"],
                    help="waqf: recitation, print and pause points 1/3 each; minimax+lsq: the 50/50 mix only; "
                         "penalized: mid-phrase rub' at a cost")
    ap.add_argument("--mid-phrase", type=float, default=rub.MID_PHRASE,
                    help="a rub' starting inside a phrase costs like a rub' this far off (fraction; inf = never)")
    ap.add_argument("--hizb-mid-phrase", type=float, default=rub.HIZB_MID_PHRASE,
                    help="the same for a hizb start (default inf: a hizb always opens a phrase)")
    ap.add_argument("--cap", type=float, default=rub.CAP,
                    help="every rub' within this fraction of its target (1/4 hizb; joint: 1/8 juz)")
    ap.add_argument("--out", default=DATA / "rub" / "rub.tsv")
    args = ap.parse_args()

    us = rub.ayat()
    d = rub.solve(us, args.weight, args.mid_phrase, args.hizb_mid_phrase, args.cap, method=args.method,
                  objective=args.objective)
    # where splitting a phrase would help the balance: the penalized solution's mid-phrase starts
    hint = rub.solve(us, args.weight, args.mid_phrase, args.hizb_mid_phrase, args.cap, method=args.method,
                     objective="penalized")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    trad = rub.scores.traditional_starts(1)
    # rub' against 1/4 of their hizb; hizb against 1/2 of their juz
    write(out, us, d.starts, 4, set(trad), args.weight, rub_rows=True)
    write_pauses(out.parent / "phrase-pauses.tsv", us)
    write(out.parent / "hizb.tsv", us, d.hizb_starts(), 2, set(trad[::4]), args.weight, rub_rows=False)

    # phrases cut by a juz start (traditional, fixed) or by a rub' start (solver)
    by_aya = {}
    for p in phrases.load():
        for x in range(p.first, p.last + 1):
            by_aya[(p.sura, x)] = p
    juz_set = set(d.juz_starts)
    with open(out.parent / "phrase-splits.tsv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["sura", "from", "to", "split_after", "reason", "topic"])
        for i in sorted(set(d.mid_phrase) | set(hint.mid_phrase) | {j for j in d.juz_starts if not us[j].phrase_start}):
            p = by_aya[(us[i].sura, us[i].aya)]
            w.writerow([p.sura, p.first, p.last, us[i].aya - 1,
                        "juz" if i in juz_set else ("rub" if i in set(d.mid_phrase) else "balance"), p.topic])

    mixv = rub.relative(us, d.starts, rub.mix(us, args.weight), 4)
    worst = max(abs(x) for x in mixv)
    hz = rub.relative(us, d.hizb_starts(), rub.mix(us, args.weight), 2)
    meta = dict(method=args.method, objective=args.objective, weight=args.weight, mid_phrase=args.mid_phrase,
                hizb_mid_phrase=args.hizb_mid_phrase, cap=args.cap, max_rub_dev_pct=round(worst * 100, 2),
                max_hizb_dev_pct=round(max(abs(x) for x in hz) * 100, 2),
                rub_inside_phrase=len(d.mid_phrase), same_as_traditional=len(set(d.starts) & set(trad)),
                hizb_same_as_traditional=len(set(d.hizb_starts()) & set(trad[::4])),
                hizb_starts=[us[s].ref for s in d.hizb_starts()], starts=[us[s].ref for s in d.starts])
    (out.parent / "solution.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {out}: worst rub' {meta['max_rub_dev_pct']}% of 1/4 hizb, worst hizb "
          f"{meta['max_hizb_dev_pct']}%, {len(d.mid_phrase)} rub' start inside a phrase, "
          f"{meta['same_as_traditional']} of 240 starts as traditional")


if __name__ == "__main__":
    main()
