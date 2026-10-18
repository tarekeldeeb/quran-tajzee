"""Hizb and rub' inside the traditional juz (Task 4).

The 30 juz are the traditional ones (the Madina Mushaf, after Ghayth al-Naf'); only the
hizb and rub' inside each juz are re-cut. A juz holds 2 hizb of 4 rub', so each juz is
cut into 8 consecutive rub' and the second hizb starts at rub' 5.

Model
-----
The unit is the aya. Its sizes are the Task 2 scores: recitation (harakat, plus the
basmala on aya 1 of every surah except 1 and 9) and typesetting (px, plus the space that
follows it). The mix is the Task 3 one, as shares of the whole Quran:

    c_a = w * r_a / R  +  (1 - w) * p_a / P

Inside juz J, rub' q has size S_q and target T_J = (size of J) / 8. The division of J is
seven cut points (ayat where rub' 2..8 start). Exactly, for each juz independently:

    minimise   sum_q ((S_q - T_J) / T_J)^2  +  sum over cuts not at a phrase start of m^2
    subject to |S_q - T_J| / T_J <= cap

m is the mid-phrase penalty: starting a rub' inside a subject phrase (at an aya end, as
the traditional rub' do) costs as much as a rub' m off its target. The hizb start
(rub' 5) uses its own penalty, by default infinite: a hizb always opens a phrase.
The juz start itself is fixed; where it falls inside a phrase the phrase is split there.

The same exact dynamic program as Task 3 (tajzee.juz._dp) solves each juz.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import juz as juz_mod
from . import phrases as phrases_mod
from . import quran, scores

INF = float("inf")
RUB_PER_JUZ = 8
HIZB_PART = 5         # the rub' (1-based, within the juz) that opens the second hizb
MID_PHRASE = 0.10     # a rub' starting inside a phrase costs like a rub' 10% off target
HIZB_MID_PHRASE = INF  # a hizb must start at a phrase start
CAP = 0.10            # every rub' within 10% of its target (1/8 of its juz)


@dataclass(frozen=True)
class Aya:
    index: int         # 0-based, Tanzil order
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
    mid_phrase: list[int]      # rub' starts (aya indices) that fall inside a phrase

    def hizb_starts(self) -> list[int]:
        return self.starts[::4]


def solve(us: list[Aya] | None = None, weight: float = 0.5, mid_phrase: float = MID_PHRASE,
          hizb_mid_phrase: float = HIZB_MID_PHRASE, cap: float | None = CAP,
          juz_starts: list[int] | None = None) -> Division:
    """Cut every juz into 8 rub' (see the module docstring for the objective)."""
    us = us if us is not None else ayat()
    js = list(juz_starts if juz_starts is not None else traditional_juz())
    c = mix(us, weight)
    bounds = js + [len(us)]
    starts, mids = [], []
    for a, b in zip(bounds, bounds[1:]):
        pre = juz_mod._prefix(c[a:b])
        T = pre[-1] / RUB_PER_JUZ

        def arr(p):
            cost = INF if p == INF else (p * T) ** 2
            return [0.0] + [0.0 if us[i].phrase_start else cost for i in range(a + 1, b)]

        inner, hizb = arr(mid_phrase), arr(hizb_mid_phrase)
        pen = [inner] + [hizb if k == HIZB_PART else inner for k in range(1, RUB_PER_JUZ + 1)]
        bound = cap * T if cap is not None else INF
        cuts, _ = juz_mod._dp(pre, RUB_PER_JUZ, T, "lsq", bound=bound, window=b - a, pen=pen)
        starts += [a] + [a + x for x in cuts]
        mids += [a + x for x in cuts if not us[a + x].phrase_start]
    return Division(starts, js, mids)


def sizes(us: list[Aya], starts: list[int], values: list[float]) -> list[float]:
    b = list(starts) + [len(us)]
    pre = juz_mod._prefix(values)
    return [pre[y] - pre[x] for x, y in zip(b, b[1:])]


def relative(us: list[Aya], starts: list[int], values: list[float], group: int) -> list[float]:
    """Deviation of each unit from 1/group of the juz it lies in (traditional juz).

    starts are unit starts in order, `group` units per juz (8 for rub', 2 for hizb)."""
    s = sizes(us, starts, values)
    out = []
    for j in range(0, len(s), group):
        t = sum(s[j:j + group]) / group
        out += [x / t - 1 for x in s[j:j + group]]
    return out
