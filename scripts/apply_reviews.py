#!/usr/bin/env python3
"""Apply a review-marks export to the phrase list and write the result.

    python scripts/apply_reviews.py reviews/<date>/marks.json            # dry run
    python scripts/apply_reviews.py reviews/<date>/marks.json --write    # update phrases.tsv

marks.json is a list of {"seg": "2:8-10", "status": "merge" | "ok" | "split" | "topic",
"splitAfter": 9, "topic": "...", "note": "...", "at": "..."} as exported from the
review page's database.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tajzee import PHRASES_TSV, phrases, quran, reviews  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("marks")
    ap.add_argument("--phrases", default=PHRASES_TSV, help="phrase list the marks were made on")
    ap.add_argument("--out", default=None, help="where to write (default: --phrases)")
    ap.add_argument("--write", action="store_true", help="write the result (otherwise dry run)")
    ap.add_argument("--partial", action="store_true", help="phrase list covers only part of the Quran")
    args = ap.parse_args()

    ps = phrases.load(args.phrases)
    marks = {m["seg"]: m for m in json.load(open(args.marks, encoding="utf-8"))}
    res = reviews.apply(ps, marks)

    for line in res.applied:
        print("applied", line)
    for line in res.warnings:
        print("WARNING", line)
    if res.stale:
        print(f"stale (phrase no longer exists, ignored): {', '.join(res.stale)}")

    rep = phrases.validate(res.phrases, quran.load(), full=not args.partial)
    print(f"{len(ps)} -> {len(res.phrases)} phrases; validation {'OK' if rep.ok else 'FAILED'}")
    for e in rep.errors[:20]:
        print("ERROR", e)

    if args.write and rep.ok:
        phrases.save(res.phrases, args.out or args.phrases)
        print("written", args.out or args.phrases)
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
