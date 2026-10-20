#!/usr/bin/env python3
"""Rebuild data/phrases/phrases.tsv from the reading and the accepted phrase splits.

    python scripts/apply_splits.py            # report what would change
    python scripts/apply_splits.py --write    # write phrases.tsv

The phrases are the reading of the text (tajzee.reviews.reading: every split listed in a
reviews/*/splits.tsv merged back) plus every row of those files whose `decision` is
`accept`. Rows without a decision column count as accepted. So to change a decision, edit the
`decision` column, accept or reject, and run this. A newly accepted row should also get its
`topic_part1` and `topic_part2`. When they are empty, both halves keep the topic of the phrase.
"""

import argparse
import sys
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tajzee import phrases, quran, reviews  # noqa: E402


def accepted_rows():
    for path in reviews.split_files():
        for r in reviews.load_splits(path):
            if r["decision"] == "accept":
                r["_file"] = path.relative_to(ROOT)
                yield r


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    base = reviews.reading()
    cuts = defaultdict(list)  # base phrase index -> [(split_after, row)]
    errors = []
    for r in accepted_rows():
        s, cut = r["sura"], r["split_after"]
        k = next((i for i, p in enumerate(base) if p.sura == s and p.first <= cut < p.last), None)
        if k is None:
            errors.append(f"{r['_file']}: {s}:{cut + 1} is not inside a phrase of the reading")
            continue
        cuts[k].append((cut, r))
    out = []
    for i, p in enumerate(base):
        if i not in cuts:
            out.append(p)
            continue
        pts = sorted(cuts[i], key=lambda x: x[0])
        first_topic = pts[0][1].get("topic_part1", "").strip() or p.topic
        start, topic = p.first, first_topic
        for cut, r in pts:
            out.append(replace(p, first=start, last=cut, topic=topic))
            start, topic = cut + 1, r.get("topic_part2", "").strip() or p.topic
        out.append(replace(p, first=start, last=p.last, topic=topic))

    rep = phrases.validate(out, quran.load())
    now = phrases.load()
    a = {(p.sura, p.first) for p in now}
    b = {(p.sura, p.first) for p in out}
    added = sorted(b - a)
    removed = sorted(a - b)
    topics = sum(1 for p in out if (p.sura, p.first) in a and next(
        (q.topic for q in now if (q.sura, q.first) == (p.sura, p.first)), None) != p.topic)
    for e in errors:
        print("error:", e)
    print(f"reading {len(base)} phrases + {sum(len(v) for v in cuts.values())} accepted splits -> {len(out)} phrases; "
          f"validation: {'ok' if rep.ok else rep.errors}")
    print(f"against the current phrases.tsv: {len(added)} new phrase starts {[f'{s}:{x}' for s, x in added]}, "
          f"{len(removed)} removed {[f'{s}:{x}' for s, x in removed]}, {topics} topics changed")
    if args.write and rep.ok and not errors:
        phrases.save(out)
        print("wrote data/phrases/phrases.tsv; now run: make scores juz rub paper")


if __name__ == "__main__":
    main()
