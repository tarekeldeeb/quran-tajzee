#!/usr/bin/env python3
"""Check data/phrases/phrases.tsv: every aya covered once, 1..10 ayat per phrase.

    python scripts/validate_phrases.py [--phrases PATH] [--max N]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tajzee import MAX_PHRASE_AYAT, PHRASES_TSV, phrases, quran  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--phrases", default=PHRASES_TSV)
    ap.add_argument("--max", type=int, default=MAX_PHRASE_AYAT)
    ap.add_argument("--partial", action="store_true", help="allow gaps (pilot / work-in-progress lists)")
    args = ap.parse_args()

    q = quran.load()
    ps = phrases.load(args.phrases)
    rep = phrases.validate(ps, q, args.max, full=not args.partial)

    total = sum(p.size for p in ps)
    print(f"{len(ps)} phrases, {total} ayat (Quran has {len(q)}), avg {total / len(ps):.2f} ayat/phrase")
    print("sizes: " + "  ".join(f"{k}:{v}" for k, v in sorted(rep.sizes.items())))
    for e in rep.errors[:50]:
        print("ERROR", e)
    if len(rep.errors) > 50:
        print(f"... and {len(rep.errors) - 50} more")
    print("OK" if rep.ok else f"FAILED with {len(rep.errors)} errors")
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
