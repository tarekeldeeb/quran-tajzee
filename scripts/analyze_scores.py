#!/usr/bin/env python3
"""Basic numeric analysis of the phrase scores; writes docs/tasks/02-scores-analysis.md.

    python scripts/analyze_scores.py

Sections: totals; per-aya and per-phrase distributions; how the two scores relate;
density by surah; the traditional juz/hizb/rub' measured with both scores; and a
feasibility check of how evenly 30 parts can be cut at phrase boundaries.
"""

import json
import math
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tajzee import phrases, quran, scores  # noqa: E402

OUT = ROOT / "docs" / "tasks" / "02-scores-analysis.md"
JSON_OUT = scores.SCORES / "analysis.json"
LABEL = {"recitation": "Recitation (harakat)", "typeset_px": "Typesetting (px @24)"}


# ----------------------------------------------------------------- statistics
def pct(xs, p):
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def describe(xs):
    m = st.fmean(xs)
    sd = st.pstdev(xs)
    return dict(n=len(xs), total=sum(xs), mean=m, sd=sd, cv=sd / m, min=min(xs), p5=pct(xs, .05),
                p25=pct(xs, .25), median=pct(xs, .5), p75=pct(xs, .75), p95=pct(xs, .95), max=max(xs),
                max_min=max(xs) / min(xs))


def pearson(x, y):
    mx, my = st.fmean(x), st.fmean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return sxy / math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))


def ranks(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


# ----------------------------------------------------------------- partition
def balanced_cut(values, parts, lo=8, hi=200):
    """Cut a sequence into `parts` contiguous groups, minimising the squared deviation
    of each group's sum from total/parts (dynamic programming, group size lo..hi)."""
    n = len(values)
    target = sum(values) / parts
    pre = [0.0]
    for v in values:
        pre.append(pre[-1] + v)
    INF = float("inf")
    cost = [[INF] * (n + 1) for _ in range(parts + 1)]
    back = [[0] * (n + 1) for _ in range(parts + 1)]
    cost[0][0] = 0.0
    for g in range(1, parts + 1):
        for i in range(g * lo, n + 1):
            best, arg = INF, 0
            for j in range(max(0, i - hi), i - lo + 1):
                c = cost[g - 1][j]
                if c == INF:
                    continue
                c += (pre[i] - pre[j] - target) ** 2
                if c < best:
                    best, arg = c, j
            cost[g][i], back[g][i] = best, arg
    cuts, i = [], n
    for g in range(parts, 0, -1):
        cuts.append(i)
        i = back[g][i]
    return sorted(cuts)[:-1]  # internal cut positions


def group_sums(values, cuts):
    bounds = [0] + list(cuts) + [len(values)]
    return [sum(values[a:b]) for a, b in zip(bounds, bounds[1:])]


# ----------------------------------------------------------------- report
def fmt(x, nd=1):
    if isinstance(x, int) or (isinstance(x, float) and x.is_integer() and abs(x) >= 100):
        return f"{int(round(x)):,}"
    return f"{x:,.{nd}f}"


def table(rows, header):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def main() -> None:
    q = quran.load()
    ay = scores.ayat()
    k = scores.constants()
    ps = phrases.load()
    pscore = [scores.score_phrase(p) for p in ps]
    flat = [(a.sura, a.aya) for a in q.ayat]
    R = {}

    # ---- totals (with one basmala per surah opening, as recited and printed)
    n_basmala = sum(1 for s in range(1, 115) if scores.opens_with_basmala(s))
    tot = scores.score_range(flat, with_basmala=True)
    R["totals"] = dict(ayat=tot.ayat, words=tot.words, letters=tot.letters, recitation=tot.recitation,
                       typeset_em=tot.typeset_em, typeset_px=tot.typeset_px, basmalas=n_basmala,
                       lines_at_1441H_width=tot.typeset_em / 15.4376)

    # ---- distributions
    aya_rec = [ay[r].recitation for r in flat]
    aya_px = [ay[r].typeset_px for r in flat]
    ph_rec = [s.recitation for s in pscore]
    ph_px = [s.typeset_px for s in pscore]
    R["aya"] = {"recitation": describe(aya_rec), "typeset_px": describe(aya_px)}
    R["phrase"] = {"recitation": describe(ph_rec), "typeset_px": describe(ph_px)}

    # ---- relation between the scores
    R["relation"] = dict(
        aya_pearson=pearson(aya_rec, aya_px), aya_spearman=spearman(aya_rec, aya_px),
        phrase_pearson=pearson(ph_rec, ph_px), phrase_spearman=spearman(ph_rec, ph_px),
        harakat_per_em_overall=tot.recitation / tot.typeset_em,
        phrase_harakat_per_em=describe([s.recitation / s.typeset_em for s in pscore]),
        harakat_per_letter=sum(aya_rec) / sum(ay[r].letters for r in flat),
    )

    # ---- density by surah (harakat per em of print), surahs with >= 10 ayat
    by_surah = []
    for s in range(1, 115):
        rs = scores.score_range([(s, a) for a in range(1, q.counts[s] + 1)])
        by_surah.append((s, rs.ayat, rs.recitation / rs.typeset_em, rs.recitation, rs.typeset_px))
    dense = sorted((x for x in by_surah if x[1] >= 10), key=lambda x: x[2])
    R["surah_density"] = [dict(sura=s, ayat=n, harakat_per_em=d) for s, n, d, *_ in by_surah]

    # ---- traditional divisions
    trad = {}
    for name, every in (("juz", 8), ("hizb", 4), ("rub", 1)):
        starts = scores.traditional_starts(every) + [len(flat)]
        units = [scores.score_range(flat[a:b], with_basmala=True) for a, b in zip(starts, starts[1:])]
        trad[name] = {m: describe([getattr(u, m) for u in units]) for m in scores.METRICS}
        if name == "juz":
            juz_units = units
    R["traditional"] = trad
    pstart = set()
    i = 0
    for p in ps:
        pstart.add(flat.index((p.sura, p.first), i))
        i = flat.index((p.sura, p.first), i)
    jstarts = scores.traditional_starts(8)
    R["traditional_juz_starts_on_phrase_start"] = sum(1 for j in jstarts if j in pstart)
    R["traditional_juz_starts_mid_phrase"] = [
        f"{flat[j][0]}:{flat[j][1]}" for j in jstarts if j not in pstart]

    # ---- feasibility: 30 parts cut only between phrases
    with_b = []
    for p, s in zip(ps, pscore):
        b = 1 if (p.first == 1 and scores.opens_with_basmala(p.sura)) else 0
        with_b.append(dict(recitation=s.recitation + b * k.basmala_recitation,
                           typeset_px=s.typeset_px + b * k.basmala_px))
    feas = {}
    for m in scores.METRICS:
        vals = [x[m] for x in with_b]
        cuts = balanced_cut(vals, 30)
        res = {}
        for m2 in scores.METRICS:
            res[m2] = describe(group_sums([x[m2] for x in with_b], cuts))
        res["phrases_per_part"] = describe([float(x) for x in group_sums([1] * len(ps), cuts)])
        target = sum(vals) / 30
        res["max_deviation_from_target"] = max(abs(s - target) / target for s in group_sums(vals, cuts))
        res["cuts"] = [f"{ps[c].sura}:{ps[c].first}" for c in cuts]
        feas[f"balanced_by_{m}"] = res
    R["feasibility_30"] = feas
    R["largest_phrase_share_of_part"] = {
        m: max(x[m] for x in with_b) / (sum(x[m] for x in with_b) / 30) for m in scores.METRICS}

    JSON_OUT.write_text(json.dumps(R, ensure_ascii=False, indent=1))

    # ================================================================ markdown
    L = []
    w = L.append
    w("# Task 2 — Length scores: analysis\n")
    w("_Generated by `scripts/analyze_scores.py` from `data/scores/`; do not edit by hand._\n")
    w("Two scores per aya, summed per phrase (see [02-length-scores.md](02-length-scores.md) "
      "for how they are computed):\n")
    w("- **Recitation**: phonemes weighted by Hafs madd lengths, in harakat "
      "(madd 2 / 4 / 6, silent letters 0, other letters 1).")
    w(f"- **Typesetting**: natural single-line width in DigitalKhatt (QMH New Madina), in px at "
      f"{k.font_px:g} px font size.\n")

    t = R["totals"]
    w("## 1. Totals\n")
    w(table([
        ["Ayat", fmt(t["ayat"])], ["Words", fmt(t["words"])], ["Letters (written)", fmt(t["letters"])],
        ["Recitation", f"{fmt(t['recitation'])} harakat"],
        ["Typesetting", f"{fmt(t['typeset_em'])} em = {fmt(t['typeset_px'])} px"],
        ["Same, in 1441H Madina lines (15.44 em)", f"{fmt(t['lines_at_1441H_width'])} lines "
                                                   f"≈ {fmt(t['lines_at_1441H_width'] / 15)} pages of 15"],
        ["Basmala (counted once per surah opening)", f"{n_basmala} × ({k.basmala_recitation} harakat, "
                                                     f"{k.basmala_px:g} px)"],
    ], ["", "value"]))
    w("\nThe line count leaves out surah header lines; with them it matches the 604-page Mushaf.\n")

    w("## 2. Distributions\n")
    rows = []
    for unit in ("aya", "phrase"):
        for m in scores.METRICS:
            d = R[unit][m]
            rows.append([unit, LABEL[m], fmt(d["mean"]), fmt(d["sd"]), f"{d['cv']:.2f}", fmt(d["min"]),
                         fmt(d["p5"]), fmt(d["median"]), fmt(d["p95"]), fmt(d["max"]),
                         f"{d['max_min']:.0f}×"])
    w(table(rows, ["unit", "score", "mean", "sd", "CV", "min", "p5", "median", "p95", "max", "max/min"]))
    w("\nPhrases are far more even than ayat (CV about half), because the phrase rules group "
      "short ayat together. They still span a wide range, from one short aya to ten long ones.\n")
    order = sorted(range(len(ps)), key=lambda i: pscore[i].recitation)
    w("Shortest and longest phrases by recitation:\n")
    rows = [[f"{ps[i].sura}:{ps[i].first}–{ps[i].last}", ps[i].topic, pscore[i].recitation,
             fmt(pscore[i].typeset_px)] for i in order[:5] + order[-5:]]
    w(table(rows, ["phrase", "topic", "harakat", "px"]))
    w("")

    r = R["relation"]
    w("## 3. How the two scores relate\n")
    w(table([
        ["Pearson, per aya", f"{r['aya_pearson']:.4f}"], ["Spearman, per aya", f"{r['aya_spearman']:.4f}"],
        ["Pearson, per phrase", f"{r['phrase_pearson']:.4f}"],
        ["Spearman, per phrase", f"{r['phrase_spearman']:.4f}"],
        ["Harakat per em of print (whole Quran)", f"{r['harakat_per_em_overall']:.3f}"],
        ["Harakat per em, phrase CV", f"{r['phrase_harakat_per_em']['cv']:.3f}"],
        ["Harakat per written letter", f"{r['harakat_per_letter']:.3f}"],
    ], ["measure", "value"]))
    w("\nThe two scores rise and fall together, but not in fixed proportion. Density, in harakat "
      "per em of print, varies by region: it rises with long madd on the reciter's side, and falls "
      "where short ayat bring many ayah markers and spaces into the print. Juz ʿAmma is about 12% "
      "lighter per em than the long Madani surahs, and that difference accumulates over a juz "
      "(section 5).\n")
    w("Lowest and highest density surahs (≥ 10 ayat), harakat per em:\n")
    rows = [[s, quran.SURAH_NAMES[s], n, f"{d:.3f}"] for s, n, d, *_ in dense[:5] + dense[-5:]]
    w(table(rows, ["sura", "name", "ayat", "harakat/em"]))
    w("")

    w("## 4. The traditional divisions, measured\n")
    rows = []
    for name, label in (("juz", "Juz (30)"), ("hizb", "Hizb (60)"), ("rub", "Rub' (240)")):
        for m in scores.METRICS:
            d = trad[name][m]
            rows.append([label, LABEL[m], fmt(d["mean"]), fmt(d["min"]), fmt(d["max"]),
                         f"{d['cv']:.3f}", f"{d['max_min']:.2f}×"])
    w(table(rows, ["unit", "score", "mean", "min", "max", "CV", "max/min"]))
    jr = [u.recitation for u in juz_units]
    w(f"\nLongest traditional juz by recitation: juz {jr.index(max(jr)) + 1}; shortest: juz "
      f"{jr.index(min(jr)) + 1}.")
    w(f"{R['traditional_juz_starts_on_phrase_start']} of the 30 traditional juz start at a phrase "
      f"start. The others begin inside a phrase: "
      f"{', '.join(R['traditional_juz_starts_mid_phrase']) or 'none'}.\n")

    w("## 5. Feasibility: 30 parts cut between phrases\n")
    w("A quick check for Task 3, not a proposal. Phrases are grouped into 30 consecutive parts by "
      "dynamic programming, minimising each part's squared deviation from 1/30 of the total. "
      "This is done once balancing by recitation and once by typesetting, and both scores are "
      "reported for each result.\n")
    rows = []
    for key, label in (("balanced_by_recitation", "by recitation"), ("balanced_by_typeset_px", "by typesetting")):
        for m in scores.METRICS:
            d = feas[key][m]
            rows.append([label, LABEL[m], fmt(d["min"]), fmt(d["max"]), f"{d['cv']:.4f}",
                         f"{d['max_min']:.3f}×"])
    for m in scores.METRICS:
        d = trad["juz"][m]
        rows.append(["traditional juz", LABEL[m], fmt(d["min"]), fmt(d["max"]), f"{d['cv']:.4f}",
                     f"{d['max_min']:.3f}×"])
    w(table(rows, ["parts balanced", "measured by", "min", "max", "CV", "max/min"]))
    pp = feas["balanced_by_recitation"]["phrases_per_part"]
    share = R["largest_phrase_share_of_part"]
    dev = feas["balanced_by_recitation"]["max_deviation_from_target"]
    dev_t = feas["balanced_by_typeset_px"]["max_deviation_from_target"]
    w(f"\nParts hold {fmt(pp['min'], 0)}–{fmt(pp['max'], 0)} phrases (median {fmt(pp['median'], 0)}); "
      f"the parts in Juz ʿAmma hold the most, as its phrases are short. The largest phrase is "
      f"{share['recitation'] * 100:.1f}% of a part by recitation ({share['typeset_px'] * 100:.1f}% by "
      f"typesetting), which limits how exactly a cut can land. Even so, every part ends within "
      f"{dev * 100:.1f}% of the target by recitation ({dev_t * 100:.1f}% when balancing by "
      f"typesetting).\n")
    w("Cut points when balancing by recitation (first phrase of parts 2–30): "
      + ", ".join(feas["balanced_by_recitation"]["cuts"]) + "\n")

    w("## 6. Takeaways\n")
    tj = trad["juz"]["recitation"]
    fr = feas["balanced_by_recitation"]["recitation"]
    w(f"- The traditional juz vary by CV {tj['cv']:.3f} in recitation (longest/shortest "
      f"{tj['max_min']:.2f}×). Cutting only at phrase boundaries brings that to CV "
      f"{fr['cv']:.4f} ({fr['max_min']:.3f}×), so meaningful boundaries cost almost nothing in balance.")
    xr = feas["balanced_by_typeset_px"]["recitation"]
    w(f"- Recitation and typesetting correlate strongly (phrase Pearson {r['phrase_pearson']:.3f}), "
      f"but balancing only one leaves the other at CV about 0.03: parts balanced for the page "
      f"range {xr['max_min']:.2f}× in recitation, wider than the traditional juz. Serving reciters "
      "and typesetters together needs a weighted mix of the two scores, which is a decision for "
      "Task 3.")
    w("- Surah openings (title and basmala) add fixed costs that the per-aya scores leave out; "
      "Task 3 must count them, as done here for the juz totals.")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT} and {JSON_OUT}")


if __name__ == "__main__":
    main()
