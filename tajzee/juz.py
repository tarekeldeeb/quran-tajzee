"""Balanced Juz (Task 3): cut the phrase sequence into 30 consecutive parts.

Model
-----
Every phrase i has a recitation size r_i (harakat) and a typesetting size p_i (px).
Surah openings are fixed costs added to the phrase that opens the surah:

* recitation: the basmala (19 harakat) for every surah except Al-Fatiha (where it is
  aya 1) and At-Tawba (none);
* typesetting: by default none, matching the Task 2 definition (the text's own width).
  With header_weight h > 0, h times the header lines Quran-Nazm prints, each a full
  line of the 1441H Madina width (15.4376 em): two lines (title + basmala) for most
  surahs, one for Al-Fatiha and At-Tawba. Juz ʿAmma's 37 headers make it long in print
  and short in recitation, so h trades print fidelity against balance in the last juz.

The two sizes are put on one scale as shares of their totals and mixed with weight w
(w = 0.5: half recitation, half typesetting):

    c_i = w * r_i / R  +  (1 - w) * p_i / P,      sum_i c_i = 1,  target per part T = 1/30.

A juz is a run of consecutive phrases, so a division is a set of 29 cut points
0 < k_1 < ... < k_29 < n in the phrase sequence; part j holds phrases k_{j-1} .. k_j - 1
and its size is S_j = C[k_j] - C[k_{j-1}] with C the prefix sums of c.

Objective (solved exactly, lexicographically):

1. minimise the worst deviation   D* = min max_j |S_j - T|          (minimax)
2. among divisions with max_j |S_j - T| <= D*, minimise   sum_j (S_j - T)^2   (least squares)

An alternative objective, 'each', treats the two scores separately instead of mixing them:
it minimises the worst relative deviation of either score in any juz,
max_j max(|R_j/T_R - 1|, |P_j/T_P - 1|), then breaks ties by least squares on the mix.

Surah-break penalty (objective 'penalized', used whenever break_penalty > 0): a juz that
starts in the middle of a surah costs as much as a juz off its target by p (a fraction),
so with B the number of such juz:

    minimise   sum_j ((S_j - T) / T)^2  +  p^2 * B        subject to |S_j - T| / T <= cap

p = 0 gives back plain least squares; larger p trades balance for juz that open surahs.
The optional cap keeps every juz within a hard limit while the penalty pulls cuts to
surah starts. Still one exact DP: the penalty is a per-cut cost.

Both steps are dynamic programs over (parts used, phrases consumed). Contiguous
partitioning has optimal substructure, so the DP is exact, not a heuristic:

    F_k(i) = min_{j < i} [ F_{k-1}(j)  (+)  g(C[i] - C[j]) ]

with (+) = max and g = |x - T| for step 1, (+) = + and g = (x - T)^2 for step 2 (with
transitions whose |x - T| > D* removed). Runtime O(K n W) for K = 30 parts, n phrases
and a window of W phrases per part (default 300, far above any feasible part).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import phrases as phrases_mod
from . import scores

PARTS = 30
LINE_EM = 15.4376  # 1441H Madina line width, the line Quran-Nazm sets
INF = float("inf")
HEADER_WEIGHT = 0.0  # printed surah header lines in the typesetting size (0 = text only)
BREAK_PENALTY = 0.03  # juz 1-25: starting mid-surah costs like a juz 3% off target
LATE_PARTS = 5        # the last 5 juz have priority to open a surah ...
LATE_PENALTY = 0.10   # ... starting one of them mid-surah costs like a juz 10% off target
CAP = 0.05            # hard limit: every juz within 5% of the target on the mix


def header_lines(sura: int) -> int:
    """Lines a surah header takes in Quran-Nazm: title + basmala, or title only."""
    return 1 if sura in (1, 9) else 2


@dataclass(frozen=True)
class Unit:
    """One phrase with its sizes, surah-opening costs included."""
    sura: int
    first: int
    last: int
    topic: str
    ayat: int
    words: int
    recitation: float
    typeset_px: float


def units(phrase_list=None, header_weight: float = HEADER_WEIGHT) -> list[Unit]:
    """Phrases with surah-opening costs; header_weight scales the printed header lines
    (0 = text only, the default; 1 = full lines as Quran-Nazm prints them)."""
    ps = phrase_list if phrase_list is not None else phrases_mod.load()
    k = scores.constants()
    line_px = LINE_EM * k.font_px * header_weight
    out = []
    for p in ps:
        s = scores.score_phrase(p)
        rec, px = float(s.recitation), float(s.typeset_px)
        if p.first == 1:
            if scores.opens_with_basmala(p.sura):
                rec += k.basmala_recitation  # recited when the surah is opened
            px += header_lines(p.sura) * line_px
        out.append(Unit(p.sura, p.first, p.last, p.topic, s.ayat, s.words, rec, px))
    return out


def combined(us: list[Unit], w: float) -> list[float]:
    R = sum(u.recitation for u in us)
    P = sum(u.typeset_px for u in us)
    return [w * u.recitation / R + (1 - w) * u.typeset_px / P for u in us]


def _prefix(values):
    pre = [0.0]
    for v in values:
        pre.append(pre[-1] + v)
    return pre


def _dp(pre, parts, target, step, bound=INF, window=300, dev=None, pen=None):
    """Exact DP. step 'minimax' or 'lsq' on the part size pre[i]-pre[j] against target.

    bound prunes parts whose deviation exceeds it; the deviation is |S - T| unless
    dev(j, i) is given, in which case dev is used for minimax and for pruning.
    pen[j] is added (least squares only) when a part starts at phrase j > 0; pen may also
    be a list indexed by part number k (1-based), each entry such an array.
    """
    n = len(pre) - 1
    cost = [[INF] * (n + 1) for _ in range(parts + 1)]
    back = [[-1] * (n + 1) for _ in range(parts + 1)]
    cost[0][0] = 0.0
    for k in range(1, parts + 1):
        prev, cur, bk = cost[k - 1], cost[k], back[k]
        pk = pen[k] if (pen is not None and isinstance(pen[0], list)) else pen
        last_i = n - (parts - k)  # leave at least one phrase for each later part
        for i in range(k, last_i + 1):
            best, arg = INF, -1
            ci = pre[i]
            for j in range(max(k - 1, i - window), i):
                f = prev[j]
                if f == INF:
                    continue
                d = abs(ci - pre[j] - target)
                e = dev(j, i) if dev is not None else d
                if e > bound:
                    continue
                if step == "minimax":
                    c = f if f > e else e
                else:
                    c = f + d * d
                    if pk is not None and j > 0:
                        c += pk[j]
                if c < best:
                    best, arg = c, j
            cur[i], bk[i] = best, arg
    if cost[parts][n] == INF:
        raise ValueError("no feasible division")
    cuts, i = [], n
    for k in range(parts, 0, -1):
        cuts.append(i)
        i = back[k][i]
    return sorted(cuts)[:-1], cost[parts][n]


@dataclass
class Solution:
    weight: float
    cuts: list[int]                      # index of the first phrase of parts 2..30
    max_dev: float                       # D*, in units of the combined score
    sum_sq: float
    parts: list[list[Unit]] = field(default_factory=list)

    @property
    def surah_breaks(self) -> int:
        """Juz (after the first) that start in the middle of a surah."""
        return sum(1 for p in self.parts[1:] if p[0].first != 1)


def solve(us: list[Unit], weight: float = 0.5, parts: int = PARTS, objective: str = "minimax+lsq",
          window: int = 300, break_penalty: float = 0.0, cap: float | None = None,
          late_penalty: float | None = None, late_parts: int = 0) -> Solution:
    """Optimal division of `us` into `parts` consecutive groups.

    objective: 'minimax+lsq' (lexicographic), 'minimax', 'lsq', or 'each' (worst deviation
    of either score, then least squares on the mix). The project's default division uses
    break_penalty=BREAK_PENALTY, cap=CAP (see scripts/solve_juz.py).
    break_penalty p > 0 switches to the 'penalized' objective: relative least squares
    plus p^2 per juz starting mid-surah, with every juz within `cap` (fraction) if given.
    late_penalty (with late_parts = N) replaces p for the last N juz: a priority on those
    juz opening a surah; float('inf') makes it a hard requirement.
    """
    c = combined(us, weight)
    pre = _prefix(c)
    target = pre[-1] / parts
    if break_penalty > 0 or objective == "penalized" or (late_penalty and late_parts):
        def arr(p):
            cost = INF if p == INF else (p * target) ** 2
            return [0.0] + [0.0 if u.first == 1 else cost for u in us[1:]]
        early = arr(break_penalty)
        if late_penalty is not None and late_parts:
            late = arr(late_penalty)
            pen = [early] + [late if k > parts - late_parts else early for k in range(1, parts + 1)]
        else:
            pen = early
        bound = cap * target if cap is not None else INF
        cuts, _ = _dp(pre, parts, target, "lsq", bound=bound, window=window, pen=pen)
    elif objective == "each":
        pr = _prefix([u.recitation for u in us])
        pp = _prefix([u.typeset_px for u in us])
        tr, tp = pr[-1] / parts, pp[-1] / parts

        def dev(j, i):
            a = abs((pr[i] - pr[j]) / tr - 1)
            b = abs((pp[i] - pp[j]) / tp - 1)
            return a if a > b else b

        _, estar = _dp(pre, parts, target, "minimax", window=window, dev=dev)
        cuts, _ = _dp(pre, parts, target, "lsq", bound=estar * (1 + 1e-12) + 1e-15, window=window, dev=dev)
    elif objective == "lsq":
        cuts, _ = _dp(pre, parts, target, "lsq", window=window)
    else:
        cuts, dstar = _dp(pre, parts, target, "minimax", window=window)
        if objective == "minimax+lsq":
            cuts, _ = _dp(pre, parts, target, "lsq", bound=dstar * (1 + 1e-12) + 1e-15, window=window)
    bounds = [0] + cuts + [len(us)]
    sums = [pre[b] - pre[a] for a, b in zip(bounds, bounds[1:])]
    return Solution(weight, cuts, max(abs(s - target) for s in sums),
                    sum((s - target) ** 2 for s in sums),
                    [us[a:b] for a, b in zip(bounds, bounds[1:])])
