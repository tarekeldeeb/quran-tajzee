"""Apply review marks from the review page to the phrase list.

A mark is a dict keyed by phrase id (``sura:first-last``) with:

- ``status: "ok"``    – approved, no change
- ``status: "merge"`` – merge with the next phrase of the same surah (chains: a run of
                        consecutive merges collapses into one phrase)
- ``status: "split"`` – split after aya ``splitAfter``
- ``status: "topic"`` – replace the topic with ``topic``
- ``note``            – free text, kept for the record only

Marks whose id no longer matches a phrase (boundaries changed since the review)
are reported as stale and ignored.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .phrases import Phrase


@dataclass
class Result:
    phrases: list[Phrase]
    applied: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def apply(phrases: list[Phrase], marks: dict[str, dict]) -> Result:
    by_id = {p.id: p for p in phrases}
    res = Result(phrases=[])
    res.stale = sorted(k for k in marks if k not in by_id)

    # 1. topic fixes and splits, phrase by phrase
    step: list[Phrase] = []
    for p in sorted(phrases, key=lambda p: (p.sura, p.first)):
        m = marks.get(p.id, {})
        st = m.get("status")
        if st == "topic" and m.get("topic", "").strip():
            step.append(replace(p, topic=m["topic"].strip()))
            res.applied.append(f"{p.id}: topic")
        elif st == "split":
            cut = m.get("splitAfter")
            if isinstance(cut, int) and p.first <= cut < p.last:
                step.append(replace(p, last=cut))
                step.append(replace(p, first=cut + 1))
                res.applied.append(f"{p.id}: split after {cut}")
            else:
                res.warnings.append(f"{p.id}: split point {cut!r} is not inside the phrase")
                step.append(p)
        else:
            step.append(p)

    # 2. merges, chaining forward within a surah (split halves are never merge targets
    #    of their own mark, since a mark has a single status)
    out: list[Phrase] = []
    pending: Phrase | None = None
    topics: list[str] = []
    for p in step:
        if pending is not None and pending.sura == p.sura:
            pending = replace(pending, last=p.last)
            topics.append(p.topic)
        else:
            if pending is not None:
                res.warnings.append(f"{pending.id}: merge requested on the last phrase of a surah")
                out.append(replace(pending, topic=_join(topics)))
            pending, topics = p, [p.topic]
        if marks.get(_orig_id(p, by_id), {}).get("status") == "merge":
            res.applied.append(f"{_orig_id(p, by_id)}: merge with next")
            continue
        out.append(replace(pending, topic=_join(topics)))
        pending, topics = None, []
    if pending is not None:
        out.append(replace(pending, topic=_join(topics)))
        res.warnings.append(f"{pending.id}: merge requested on the last phrase of a surah")

    res.phrases = out
    return res


def _orig_id(p: Phrase, by_id: dict[str, Phrase]) -> str:
    return p.id if p.id in by_id else ""


def _join(topics: list[str]) -> str:
    seen: list[str] = []
    for t in topics:
        if t not in seen:
            seen.append(t)
    return "، ".join(seen)


DIVISION_KINDS = ("juz", "hizb", "rub", "balance")


def load_splits(path) -> list[dict]:
    """Rows of a split round (reviews/*/splits.tsv), normalised.

    File columns, base first, then the proposal:
      juz               the juz the row is about
      kind              hizb: an optional start for the juz's second hizb;
                        juz: the traditional juz start (fixed, so the split is required)
      base_start        where the second hizb started before this round (hizb rows)
      base_balance      its balance: first hizb against half the juz
      proposed_start    the aya proposed as a new phrase start (and hizb start)
      proposed_balance  the balance if the second hizb started there
      inside_phrase     the existing phrase (sura:from-to) that the proposed start splits
      decision          accept or reject
      why               the reason for the decision
      topic_part1/2     topics of the two phrases the split would make
    Returned keys add sura, split_after, from, to (ints) for the code.
    """
    import csv

    out = []
    for r in csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"):
        s, a = map(int, r["proposed_start"].split(":"))
        ps, rng = r["inside_phrase"].split(":")
        f, t = map(int, rng.split("-"))
        r = dict(r, sura=s, split_after=a - 1, **{"from": f, "to": t})
        r["decision"] = (r.get("decision") or "accept").strip()
        out.append(r)
    return out


def split_files(root=None):
    from pathlib import Path

    from . import ROOT
    return sorted(Path(root or ROOT / "reviews").glob("*/splits.tsv"))


def reading(phrases: list[Phrase] | None = None, rounds_dir=None) -> list[Phrase]:
    """The phrase list as a reading of the text alone.

    Every split listed in a reviews/*/splits.tsv (accepted or not) is merged back, keeping the
    topic of the first half. Use this when judging whether a traditional boundary falls inside
    a subject phrase. Otherwise the splits made to follow those very boundaries would hide the cuts.
    """
    from . import phrases as phrases_mod

    ps = list(phrases if phrases is not None else phrases_mod.load())
    joins = {(r["sura"], r["split_after"] + 1) for path in split_files(rounds_dir)
             for r in load_splits(path) if r["kind"] in DIVISION_KINDS}
    out: list[Phrase] = []
    for p in ps:
        if out and (p.sura, p.first) in joins and out[-1].sura == p.sura and out[-1].last + 1 == p.first:
            out[-1] = replace(out[-1], last=p.last)
        else:
            out.append(p)
    return out
