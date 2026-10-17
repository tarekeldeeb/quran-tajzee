#!/usr/bin/env python3
"""Build the self-contained review page (build/review.html) from phrases.tsv.

    python scripts/build_review.py [--phrases PATH] [--out build/review.html]

The page embeds the Tanzil text and the phrase list, and stores review marks in the
hosting artifact's database (collection "reviews", one document per phrase id).
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tajzee import PHRASES_TSV, phrases, quran  # noqa: E402

TEMPLATE = ROOT / "review" / "template.html"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--phrases", default=PHRASES_TSV)
    ap.add_argument("--out", default=ROOT / "build" / "review.html")
    args = ap.parse_args()

    q = quran.load()
    data = [
        {
            "id": p.id,
            "s": p.sura,
            "f": p.first,
            "t": p.last,
            "topic": p.topic,
            "ayat": [a.text for a in q.range(p.sura, p.first, p.last)],
        }
        for p in phrases.load(args.phrases)
    ]
    names = {s: n for s, n in quran.SURAH_NAMES.items() if any(d["s"] == s for d in data)}

    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    html = html.replace("__NAMES__", json.dumps(names, ensure_ascii=False))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB, {len(data)} phrases)")


if __name__ == "__main__":
    main()
