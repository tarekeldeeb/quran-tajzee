#!/usr/bin/env python3
"""Print a compact, diacritic-free view of a range of ayat, one per line.

Useful for reading a passage quickly when choosing phrase boundaries:

    python scripts/dump_text.py 2:142 2:286          # whole ayat
    python scripts/dump_text.py 18 --words 8         # a surah, first 8 words of each aya
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tajzee import quran  # noqa: E402


def parse_ref(s: str, q, end: bool) -> tuple[int, int]:
    if ":" in s:
        a, b = s.split(":")
        return int(a), int(b)
    sura = int(s)
    return (sura, q.counts[sura]) if end else (sura, 1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("start", help="sura or sura:aya")
    ap.add_argument("end", nargs="?", help="sura or sura:aya (default: end of start's surah)")
    ap.add_argument("--words", type=int, default=0, help="truncate each aya to N words")
    args = ap.parse_args()

    q = quran.load()
    lo = parse_ref(args.start, q, end=False)
    hi = parse_ref(args.end or args.start.split(":")[0], q, end=True)
    for a in q.ayat:
        if lo <= (a.sura, a.aya) <= hi:
            words = quran.plain(a.text).split()
            if args.words and len(words) > args.words:
                words = words[: args.words] + ["…"]
            print(a.ref, " ".join(words))


if __name__ == "__main__":
    main()
