"""The subject-phrase segmentation (Task 1): a list of (sura, from, to, topic).

``data/phrases/phrases.tsv`` is the single source of truth. Every other format
(the review page, JSON exports, later Juz work) is generated from it.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from . import MAX_PHRASE_AYAT, PHRASES_TSV
from .quran import Quran

HEADER = ["sura", "from", "to", "topic"]


@dataclass(frozen=True)
class Phrase:
    sura: int
    first: int
    last: int
    topic: str

    @property
    def id(self) -> str:
        """Stable key, also used by the review page: ``sura:first-last``."""
        return f"{self.sura}:{self.first}-{self.last}"

    @property
    def size(self) -> int:
        return self.last - self.first + 1


def load(path: Path | str = PHRASES_TSV) -> list[Phrase]:
    with open(path, encoding="utf-8", newline="") as fh:
        rows = csv.reader(fh, delimiter="\t")
        header = next(rows)
        if header != HEADER:
            raise ValueError(f"{path}: expected header {HEADER}, got {header}")
        return [Phrase(int(s), int(f), int(t), topic) for s, f, t, topic in rows]


def save(phrases: list[Phrase], path: Path | str = PHRASES_TSV) -> None:
    phrases = sorted(phrases, key=lambda p: (p.sura, p.first))
    with open(path, "w", encoding="utf-8", newline="") as fh:
        out = csv.writer(fh, delimiter="\t", lineterminator="\n")
        out.writerow(HEADER)
        for p in phrases:
            out.writerow([p.sura, p.first, p.last, p.topic])


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    sizes: Counter = field(default_factory=Counter)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate(
    phrases: list[Phrase], quran: Quran, max_ayat: int = MAX_PHRASE_AYAT, full: bool = True
) -> Report:
    """Check the segmentation covers every aya exactly once with phrases of 1..max_ayat.

    With ``full=False`` (a partial list, e.g. a pilot) gaps are allowed; overlaps are not.
    """
    rep = Report()
    seen: Counter = Counter()
    for p in phrases:
        rep.sizes[p.size] += 1
        if p.last < p.first:
            rep.errors.append(f"{p.id}: ends before it starts")
            continue
        if p.size > max_ayat:
            rep.errors.append(f"{p.id}: {p.size} ayat (max {max_ayat})")
        if not p.topic.strip():
            rep.errors.append(f"{p.id}: empty topic")
        for a in range(p.first, p.last + 1):
            if (p.sura, a) not in quran:
                rep.errors.append(f"{p.id}: aya {p.sura}:{a} does not exist")
            seen[(p.sura, a)] += 1
    for a in quran.ayat:
        n = seen[(a.sura, a.aya)]
        if n == 0 and full:
            rep.errors.append(f"{a.ref}: not covered by any phrase")
        elif n > 1:
            rep.errors.append(f"{a.ref}: covered by {n} phrases")
    return rep
