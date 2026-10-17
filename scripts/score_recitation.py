#!/usr/bin/env python3
"""Recitation score of every aya: phoneme count weighted by Hafs madd lengths.

Source of truth: tarekeldeeb/tajweed-embeddings (one vector per letter, with tajweed
rule flags from the cpfair/quran-tajweed decision trees, Hafs 'an 'Asim).

Model
  * Each aya is recited on its own: begun (ibtida') at its first word and stopped
    (waqf) on its last word; inside the aya the recitation is continuous (wasl).
    This uses the embedder's start/stop variants, so hamzat al-wasl is voiced at
    the start and madd 'arid lil-sukun appears at the stop.
  * A letter that is written but not pronounced counts 0: rule flags silent,
    hamzat_wasl (mid-aya) and lam_shamsiyyah.
  * A madd letter counts its length in harakat (see MADD below); when several madd
    flags meet on one letter the longest wins.
  * Every other letter counts 1 (shadda, ghunnah, qalqalah etc. are not weighted).
  * The basmala that this Tanzil text prefixes to aya 1 of every surah except
    Al-Fatiha (where it is aya 1) and At-Tawba (none) is not part of the aya: it is
    scored separately, once, as data/scores/basmala_recitation.tsv, and the aya starts (ibtida')
    at its own first word.

Output: data/scores/recitation_ayat.tsv

    TAJWEED_EMBEDDINGS=../tajweed-embeddings python scripts/score_recitation.py
"""

import argparse
import csv
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tajzee import DATA, quran  # noqa: E402

MADD = {
    "madd_2": 2,         # madd tabi'i, and the badal/'iwad/sila forms the embedder maps to it
    "madd_munfasil": 4,  # detached: 4 harakat (Hafs via al-Shatibiyya; tawassut)
    "madd_muttasil": 4,  # attached: 4 harakat (Hafs via al-Shatibiyya; tawassut)
    "madd_246": 4,       # 'arid lil-sukun at a stop: 2, 4 or 6 allowed; 4 (tawassut) taken
    "madd_6": 6,         # lazim: 6 harakat
}
SILENT = ("silent", "hamzat_wasl", "lam_shamsiyyah")
COLUMNS = ["sura", "aya", "letters", "silent", "plain", "madd2", "madd4", "madd6", "score"]


BASMALA_WORDS = 4


def has_basmala(sura: int, aya: int) -> bool:
    return aya == 1 and sura not in (1, 9)


def score_aya(emb, rule_start, idx, skip_words=0):
    """Score one embedded aya, recited from word `skip_words` to its end with a stop."""
    n = len(emb.words)
    vecs = emb.realize(stop_words=[n - 1], start_words=[skip_words])
    vecs = vecs[emb.words[skip_words][0]:]
    c = Counter(letters=len(vecs))
    total = 0
    for v in vecs:
        rules = {name for name, i in idx.items() if v[rule_start + i] > 0}
        madd = max((MADD[r] for r in rules if r in MADD), default=0)
        if madd:
            c[f"madd{madd}"] += 1
            total += madd
        elif rules & set(SILENT):
            c["silent"] += 1
        else:
            c["plain"] += 1
            total += 1
    c["score"] = total
    return c


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--embeddings", default=os.environ.get("TAJWEED_EMBEDDINGS",
                                                          ROOT.parent / "tajweed-embeddings"))
    ap.add_argument("--out", default=DATA / "scores" / "recitation_ayat.tsv")
    args = ap.parse_args()

    sys.path.insert(0, str(Path(args.embeddings) / "src"))
    from tajweed_embeddings import TajweedEmbedder

    emb = TajweedEmbedder()
    rule_start = emb.embedding_dim - len(emb.rule_names)  # rule flags are the last slice
    idx = {name: i for i, name in enumerate(emb.rule_names)}

    q = quran.load()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(COLUMNS)
        for k, a in enumerate(q.ayat):
            skip = BASMALA_WORDS if has_basmala(a.sura, a.aya) else 0
            c = score_aya(emb.text_to_embedding(a.sura, a.aya), rule_start, idx, skip)
            w.writerow([a.sura, a.aya] + [c[col] for col in COLUMNS[2:]])
            if k % 500 == 0:
                print(f"{a.ref} ...", file=sys.stderr)
    print(f"wrote {out}")

    # The basmala as recited when opening a surah (scored from Al-Fatiha 1:1).
    b = score_aya(emb.text_to_embedding(1, 1), rule_start, idx)
    with open(out.parent / "basmala_recitation.tsv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(COLUMNS[2:])
        w.writerow([b[col] for col in COLUMNS[2:]])


if __name__ == "__main__":
    main()
