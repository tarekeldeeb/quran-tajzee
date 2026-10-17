"""Length scores (Task 2): recitation and typesetting size of ayat, phrases and ranges.

The per-aya scores in ``data/scores/*_ayat.tsv`` are produced by
``scripts/score_recitation.py`` and ``scripts/score_typesetting.py`` from the external
source-of-truth projects. Everything here only reads those files, so later tasks need
neither project installed.

- recitation: harakat-weighted phoneme count (madd 2/4/6 per Hafs, silent letters 0)
- typeset_em / typeset_px: natural single-line width in DigitalKhatt, in em and in px
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from functools import lru_cache

from . import DATA
from .phrases import Phrase

SCORES = DATA / "scores"
RUB_STARTS = DATA / "source" / "hafs-rub-start-ayahs.json"
METRICS = ("recitation", "typeset_px")


@dataclass(frozen=True)
class AyaScore:
    sura: int
    aya: int
    words: int
    letters: int
    recitation: int
    typeset_em: float
    typeset_px: float


@dataclass(frozen=True)
class Constants:
    space_em: float
    space_px: float
    font_px: float
    basmala_recitation: int
    basmala_em: float
    basmala_px: float


def _rows(name: str):
    with open(SCORES / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


@lru_cache(maxsize=None)
def ayat() -> dict[tuple[int, int], AyaScore]:
    rec = {(int(r["sura"]), int(r["aya"])): r for r in _rows("recitation_ayat.tsv")}
    out = {}
    for r in _rows("typesetting_ayat.tsv"):
        key = (int(r["sura"]), int(r["aya"]))
        out[key] = AyaScore(key[0], key[1], int(r["words"]), int(rec[key]["letters"]),
                            int(rec[key]["score"]), float(r["em"]), float(r["px"]))
    return out


@lru_cache(maxsize=None)
def constants() -> Constants:
    c = {r["name"]: r for r in _rows("typesetting_constants.tsv")}
    b_rec = _rows("basmala_recitation.tsv")[0]
    b_ts = _rows("basmala_typesetting.tsv")[0]
    return Constants(float(c["space"]["em"]), float(c["space"]["px"]), float(c["font_px"]["px"]),
                     int(b_rec["score"]), float(b_ts["em"]), float(b_ts["px"]))


def opens_with_basmala(sura: int) -> bool:
    """Surahs whose recitation and print open with a basmala that is not an aya."""
    return sura not in (1, 9)


@dataclass(frozen=True)
class RangeScore:
    ayat: int
    words: int
    letters: int
    recitation: int
    typeset_em: float
    typeset_px: float


def score_range(refs: list[tuple[int, int]], with_basmala: bool = False) -> RangeScore:
    """Scores of consecutive ayat set as one line (one space between ayat).

    with_basmala adds the basmala for every surah that starts inside the range,
    the way a reciter recites it and a Mushaf prints it.
    """
    a = ayat()
    k = constants()
    rows = [a[r] for r in refs]
    em = sum(x.typeset_em for x in rows) + k.space_em * max(len(rows) - 1, 0)
    px = sum(x.typeset_px for x in rows) + k.space_px * max(len(rows) - 1, 0)
    rec = sum(x.recitation for x in rows)
    if with_basmala:
        n = sum(1 for x in rows if x.aya == 1 and opens_with_basmala(x.sura))
        rec += n * k.basmala_recitation
        em += n * k.basmala_em
        px += n * k.basmala_px
    return RangeScore(len(rows), sum(x.words for x in rows), sum(x.letters for x in rows),
                      rec, round(em, 4), round(px, 1))


def score_phrase(p: Phrase) -> RangeScore:
    return score_range([(p.sura, n) for n in range(p.first, p.last + 1)])


def traditional_starts(every: int) -> list[int]:
    """Global aya indices (0-based) where each traditional unit starts.

    every=1: rub' (240), 4: hizb (60), 8: juz (30).
    """
    marks = json.loads(RUB_STARTS.read_text())
    return [marks[k] - 1 for k in range(1, 241, every)]
