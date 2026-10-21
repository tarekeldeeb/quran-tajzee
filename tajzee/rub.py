"""Hizb and rub' inside the traditional juz (Task 4).

The 30 juz are the traditional ones (the Madina Mushaf, after Ghayth al-Naf'); only the
hizb and rub' inside each juz are re-cut. A juz holds 2 hizb of 4 rub'.

Every new boundary opens a phrase (a hard rule, objective 'minimax+lsq', the default). The
older 'penalized' objective may start a rub' inside a phrase at a penalty; it is kept to
suggest phrase splits that would improve the balance.

Two methods, both exact:

* nested (default), the way the divisions nest: first each juz is cut into its 2 hizb
  (target 1/2 of the juz), then each hizb into its 4 rub' (target 1/4 of the hizb). The
  hizb are as even as the phrases allow, and each quarter is balanced within its hizb.
* joint: each juz is cut into 8 rub' at once (target 1/8 of the juz); the second hizb
  starts at rub' 5.

Model
-----
The unit is the aya. Its sizes are the Task 2 scores: recitation (harakat, plus the
basmala on aya 1 of every surah except 1 and 9) and typesetting (px, plus the space that
follows it). The mix is the Task 3 one, as shares of the whole Quran:

    c_a = w * r_a / R  +  (1 - w) * p_a / P

A container G (a juz, or a hizb) is cut into k parts (2 hizb, or 4 rub') with target
T_G = (size of G) / k. Exactly, for each container independently:

    minimax+lsq (default): cuts only at phrase starts;
        1. minimise the worst  |S_q - T_G| / T_G,
        2. among those, minimise  sum_q (S_q - T_G)^2.
    penalized:
        minimise   sum_q ((S_q - T_G) / T_G)^2  +  sum over cuts not at a phrase start of m^2
        subject to |S_q - T_G| / T_G <= cap

m is the mid-phrase penalty: starting a rub' inside a subject phrase (at an aya end, as
the traditional rub' do) costs as much as a rub' m off its target. A hizb start uses its
own penalty, by default infinite: a hizb always opens a phrase. No hizb or rub' starts at
aya 2..7 of any surah (HEAD_AYAT): it starts at the surah itself or at aya 8 or later. Juz 28
is exempt (HEAD_EXEMPT_JUZ): its short surahs leave too few admissible starts. Every boundary
is also an aya end agreed by all six counting systems (disputed_end). The juz
starts are fixed and exempt; where one falls inside a phrase the phrase is split there.

The same exact dynamic program as Task 3 (tajzee.juz._dp) solves each container.
"""

from __future__ import annotations

import bisect

from dataclasses import dataclass

from . import juz as juz_mod
from . import phrases as phrases_mod
from . import quran, scores

INF = float("inf")
RUB_PER_JUZ = 8
HIZB_PART = 5          # joint method: the rub' (1-based, within the juz) that opens the second hizb
METHOD = "nested"
OBJECTIVE = "minimax+lsq"  # every boundary at a phrase start; 'penalized' allows mid-phrase rub'
MID_PHRASE = 0.10      # a rub' starting inside a phrase costs like a rub' 10% off target
HIZB_MID_PHRASE = INF  # a hizb must start at a phrase start
HEAD_AYAT = 7          # no rub' starts at aya 2..7 of a surah: at the surah start, or at aya 8 or later
HEAD_MIN_SURAH = 0     # ... in every surah, whatever its length
HEAD_EXEMPT_JUZ = {28}  # ... except in these juz (28: its short surahs leave too few admissible starts)
CAP = 0.10             # every rub' within 10% of its target (1/4 of its hizb; joint: 1/8 of its juz)


@dataclass(frozen=True)
class Aya:
    index: int          # 0-based, Tanzil order
    sura: int
    aya: int
    recitation: float
    typeset_px: float
    phrase_start: bool  # the aya opens a Task 1 phrase
    topic: str          # topic of the phrase it belongs to

    @property
    def ref(self) -> str:
        return f"{self.sura}:{self.aya}"


def ayat(phrase_list=None) -> list[Aya]:
    ps = phrase_list if phrase_list is not None else phrases_mod.load()
    topic, start = {}, set()
    for p in ps:
        start.add((p.sura, p.first))
        for n in range(p.first, p.last + 1):
            topic[(p.sura, n)] = p.topic
    a = scores.ayat()
    k = scores.constants()
    out = []
    for i, x in enumerate(quran.load().ayat):
        s = a[(x.sura, x.aya)]
        rec = float(s.recitation)
        if x.aya == 1 and scores.opens_with_basmala(x.sura):
            rec += k.basmala_recitation
        out.append(Aya(i, x.sura, x.aya, rec, s.typeset_px + k.space_px,
                       (x.sura, x.aya) in start, topic[(x.sura, x.aya)]))
    return out


def mix(us: list[Aya], w: float = 0.5) -> list[float]:
    R = sum(u.recitation for u in us)
    P = sum(u.typeset_px for u in us)
    return [w * u.recitation / R + (1 - w) * u.typeset_px / P for u in us]


def traditional_juz() -> list[int]:
    """Aya index where each traditional juz starts."""
    return scores.traditional_starts(8)


@dataclass
class Division:
    starts: list[int]          # 240 aya indices, the first aya of each rub'
    juz_starts: list[int]      # 30 aya indices (fixed)
    mid_phrase: list[int]      # rub' starts (aya indices, juz starts excluded) inside a phrase

    def hizb_starts(self) -> list[int]:
        return self.starts[::4]


HIZB_APPROVED = "hizb-approved.tsv"


def fixed_hizb(us: list[Aya]) -> list[int] | None:
    """The 60 approved hizb starts (aya indices), or None if there is no approved list."""
    from . import DATA
    path = DATA / "rub" / HIZB_APPROVED
    if not path.exists() or len(us) != len(quran.load().ayat):
        return None
    idx = {(u.sura, u.aya): u.index for u in us}
    out = []
    for line in path.read_text().splitlines()[1:]:
        s, a = map(int, line.split("\t")[1].split(":"))
        i = idx[(s, a)]
        if i not in set(traditional_juz()) and (not us[i].phrase_start or in_head(us[i])):
            raise ValueError(f"approved hizb start {s}:{a} is not a phrase start or is in a surah's first ayat")
        out.append(i)
    return out


_COUNTS = None
_JUZ = None


def in_head(u: Aya, head: int = HEAD_AYAT, min_surah: int = HEAD_MIN_SURAH) -> bool:
    """The aya is one of the first `head` ayat of a surah of `min_surah`+ ayat, but not its
    first: no rub' may start there."""
    global _COUNTS, _JUZ
    if not 2 <= u.aya <= head:
        return False
    if _COUNTS is None:
        _COUNTS = quran.load().counts
        _JUZ = traditional_juz()
    if bisect.bisect_right(_JUZ, u.index) in HEAD_EXEMPT_JUZ:
        return False
    return _COUNTS.get(u.sura, 0) >= min_surah


COUNTING_SYSTEMS = {"kufi", "madani-first", "madani-last", "makki", "basri", "dimashqi"}
_PRIMITIVES = None


def disputed_end(u: Aya) -> list[str]:
    """Counting systems that do NOT count the end of the aya before `u` as an aya end.

    Empty when the boundary before `u` is agreed by all six systems (فاصلة بلا خلاف), as
    al-Ṣafāqusī requires of every division end. Source: al-Dānī's al-Bayān via
    quranpedia/qiraat-ayah-map (data/source/counting/)."""
    global _PRIMITIVES
    if u.aya == 1:
        return []  # a surah end is agreed by all
    if _PRIMITIVES is None:
        import json
        from . import DATA
        _PRIMITIVES = json.loads((DATA / "source" / "counting" / "book-boundary-primitives.json")
                                 .read_text(encoding="utf-8"))["surahs"]
    e = _PRIMITIVES.get(str(u.sura), {}).get(str(u.aya - 1), {}).get("end")
    return sorted(COUNTING_SYSTEMS - set(e["counted_by"])) if e else []


def blocked(u: Aya, head: int = HEAD_AYAT) -> bool:
    """No hizb or rub' may start at `u`: an opening aya of a surah, or a disputed aya end."""
    return in_head(u, head) or bool(disputed_end(u))


def _cut_phrases(us, c, a, b, parts, head=HEAD_AYAT):
    """Exact minimax-then-least-squares cut of ayat a..b-1 into `parts`, at phrase starts only,
    never at aya 2..head of a surah."""
    pre = juz_mod._prefix(c[a:b])
    T = pre[-1] / parts
    BIG = 1e9  # deviation of a part starting at an inadmissible aya: never chosen while any other is feasible

    def dev(j, i):
        if j > 0 and (not us[a + j].phrase_start or blocked(us[a + j], head)):
            return BIG
        return abs(pre[i] - pre[j] - T)

    _, e = juz_mod._dp(pre, parts, T, "minimax", window=b - a, dev=dev)
    if e >= BIG:
        raise ValueError("not enough phrase starts")
    cuts, _ = juz_mod._dp(pre, parts, T, "lsq", bound=e * (1 + 1e-12) + 1e-15, window=b - a, dev=dev)
    return [a] + [a + x for x in cuts]


def _cut(us, c, a, b, parts, pen_for, cap, head=HEAD_AYAT):
    """Exact cut of ayat a..b-1 into `parts`; pen_for(k) is the mid-phrase penalty of part k.
    No part starts at aya 2..head of a surah."""
    pre = juz_mod._prefix(c[a:b])
    T = pre[-1] / parts

    def arr(p):
        cost = INF if p == INF else (p * T) ** 2
        return [0.0] + [INF if blocked(us[i], head) else (0.0 if us[i].phrase_start else cost)
                        for i in range(a + 1, b)]

    cache = {}
    for k in range(1, parts + 1):
        cache.setdefault(pen_for(k), None)
    for p in cache:
        cache[p] = arr(p)
    pen = [cache[pen_for(1)]] + [cache[pen_for(k)] for k in range(1, parts + 1)]
    bound = cap * T if cap is not None else INF
    try:
        cuts, _ = juz_mod._dp(pre, parts, T, "lsq", bound=bound, window=b - a, pen=pen)
    except ValueError:
        if bound == INF:
            raise
        # the cap cannot be met here (e.g. under the opening-ayat rule): solve this container without it
        cuts, _ = juz_mod._dp(pre, parts, T, "lsq", bound=INF, window=b - a, pen=pen)
    return [a] + [a + x for x in cuts]


def solve(us: list[Aya] | None = None, weight: float = 0.5, mid_phrase: float = MID_PHRASE,
          hizb_mid_phrase: float = HIZB_MID_PHRASE, cap: float | None = CAP,
          juz_starts: list[int] | None = None, method: str = METHOD,
          objective: str = OBJECTIVE, pin_hizb: bool = True,
          head_ayat: int = HEAD_AYAT) -> Division:
    """Cut every juz into 2 hizb of 4 rub' (see the module docstring for the objective).

    With the default objective and the traditional juz, the hizb approved in review
    (data/rub/hizb-approved.tsv) are kept as they are, if that file exists; pin_hizb=False
    re-solves them.

    mid_phrase, hizb_mid_phrase and cap apply to the 'penalized' objective only."""
    us = us if us is not None else ayat()
    js = list(juz_starts if juz_starts is not None else traditional_juz())
    c = mix(us, weight)
    end = [len(us)]
    starts = []
    if objective == "minimax+lsq":
        parts_by = {"nested": None, "joint": RUB_PER_JUZ}
        if method not in parts_by:
            raise ValueError(f"unknown method {method!r}")
        if method == "nested":
            hizb = fixed_hizb(us) if (juz_starts is None and pin_hizb) else None
            if hizb is None:
                hizb = []
                for a, b in zip(js, js[1:] + end):
                    hizb += _cut_phrases(us, c, a, b, 2, head_ayat)
            for a, b in zip(hizb, hizb[1:] + end):
                starts += _cut_phrases(us, c, a, b, 4, head_ayat)
        else:
            for a, b in zip(js, js[1:] + end):
                starts += _cut_phrases(us, c, a, b, RUB_PER_JUZ, head_ayat)
    elif objective != "penalized":
        raise ValueError(f"unknown objective {objective!r}")
    elif method == "nested":
        hizb = []
        for a, b in zip(js, js[1:] + end):
            hizb += _cut(us, c, a, b, 2, lambda k: hizb_mid_phrase, None, head_ayat)
        for a, b in zip(hizb, hizb[1:] + end):
            starts += _cut(us, c, a, b, 4, lambda k: mid_phrase, cap, head_ayat)
    elif method == "joint":
        for a, b in zip(js, js[1:] + end):
            starts += _cut(us, c, a, b, RUB_PER_JUZ,
                           lambda k: hizb_mid_phrase if k == HIZB_PART else mid_phrase, cap, head_ayat)
    else:
        raise ValueError(f"unknown method {method!r}")
    jset = set(js)
    mids = [s for s in starts if s not in jset and not us[s].phrase_start]
    return Division(starts, js, mids)


def sizes(us: list[Aya], starts: list[int], values: list[float]) -> list[float]:
    b = list(starts) + [len(us)]
    pre = juz_mod._prefix(values)
    return [pre[y] - pre[x] for x, y in zip(b, b[1:])]


def relative(us: list[Aya], starts: list[int], values: list[float], group: int) -> list[float]:
    """Deviation of each unit from 1/group of the container it lies in.

    starts are unit starts in order, `group` units per container: 8 rub' or 2 hizb per juz,
    4 rub' per hizb."""
    s = sizes(us, starts, values)
    out = []
    for j in range(0, len(s), group):
        t = sum(s[j:j + group]) / group
        out += [x / t - 1 for x in s[j:j + group]]
    return out
