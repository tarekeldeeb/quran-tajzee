#!/usr/bin/env python3
"""Apply a round of phrase splits (with a topic for each half) to data/phrases/phrases.tsv.

    python scripts/apply_splits.py reviews/2026-10-18-hizb-splits/splits.tsv [--write]

The splits file has columns sura, from, to, split_after, reason, topic_first, topic_second,
note. Each row must match an existing phrase exactly. Without --write, it only reports.
"""

import argparse
import csv
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tajzee import phrases, quran  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("splits")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    ps = phrases.load()
    index = {(p.sura, p.first, p.last): i for i, p in enumerate(ps)}
    out, done, errors = list(ps), 0, []
    rows = list(csv.DictReader(open(args.splits, encoding="utf-8"), delimiter="\t"))
    repl = {}
    for r in rows:
        key = (int(r["sura"]), int(r["from"]), int(r["to"]))
        cut = int(r["split_after"])
        if key not in index:
            errors.append(f"{key}: no such phrase (already split?)")
            continue
        p = ps[index[key]]
        if not p.first <= cut < p.last:
            errors.append(f"{p.id}: split point {cut} not inside")
            continue
        repl[index[key]] = [replace(p, last=cut, topic=r["topic_first"]),
                            replace(p, first=cut + 1, topic=r["topic_second"])]
        done += 1
    out = [q for i, p in enumerate(ps) for q in repl.get(i, [p])]
    rep = phrases.validate(out, quran.load())
    for e in errors:
        print("error:", e)
    print(f"{done} splits, {len(ps)} -> {len(out)} phrases; validation: {'ok' if rep.ok else rep.errors}")
    if args.write and rep.ok and not errors:
        phrases.save(out)
        print("wrote data/phrases/phrases.tsv")


if __name__ == "__main__":
    main()
