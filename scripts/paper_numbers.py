#!/usr/bin/env python3
"""Write paper/numbers.tex: every number the paper quotes, as LaTeX macros.

    python scripts/paper_numbers.py

The paper uses only these macros for results, so `make paper` keeps it in sync with the data.
"""

import bisect
import collections
import csv
import dataclasses
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tajzee import DATA, phrases, quran, reviews, rub, scores, waqf  # noqa: E402

INF = float("inf")


def main() -> None:
    m = {}
    q = quran.load()
    ps = phrases.load()
    m["Ayat"] = f"{len(q.ayat):,}"
    m["Phrases"] = f"{len(ps):,}"
    m["PhrasesReading"] = f"{len(reviews.reading()):,}"
    m["PhraseMean"] = f"{len(q.ayat) / len(ps):.1f}"
    s2 = json.loads((DATA / "scores" / "analysis.json").read_text())
    m["PearsonAya"] = f"{s2['relation']['aya_pearson']:.3f}"
    m["PearsonPhrase"] = f"{s2['relation']['phrase_pearson']:.3f}"
    m["RecitationTotal"] = f"{s2['totals']['recitation']:,}"

    # letters (written, without basmala) and equal-letter positions
    def words(a):
        w = quran.plain(a.text).split()
        return w[4:] if a.aya == 1 and a.sura not in (1, 9) else w
    letters = [sum(len(x) for x in words(a)) for a in q.ayat]
    cum = [0]
    for x in letters:
        cum.append(cum[-1] + x)
    total = cum[-1]
    m["Letters"] = f"{total:,}"
    trad = scores.traditional_starts(1)
    js = trad[::8]
    unit = total / 30
    m["JuzOff"] = f"{st.mean(abs(cum[js[k]] - k * unit) / unit for k in range(1, 30)) * 100:.1f}"
    off, floor = [], []
    jb = js + [len(letters)]
    for j in range(30):
        a, b = jb[j], jb[j + 1]
        u = (cum[b] - cum[a]) / 8
        for k in range(1, 8):
            P = cum[a] + k * u
            off.append(abs(cum[trad[8 * j + k]] - P) / u)
            i = bisect.bisect_left(cum, P)
            floor.append(min(abs(cum[x] - P) for x in (i - 1, i)) / u)
    m["RubOff"] = f"{st.mean(off) * 100:.0f}"
    m["RubFloor"] = f"{st.mean(floor) * 100:.1f}"
    m["RubExcess"] = f"{st.mean(off) / st.mean(floor):.0f}"
    sizes = [cum[b] - cum[a] for a, b in zip(trad, trad[1:] + [len(letters)])]
    m["RubLetterSpread"] = f"{max(sizes) / min(sizes):.1f}"

    # phrase cuts of the traditional boundaries (against the reading)
    rows = list(csv.DictReader(open(DATA / "rub" / "traditional-rub.tsv", encoding="utf-8"), delimiter="\t"))
    inside = [r for r in rows[1:] if r["inside_phrase"] == "1"]
    m["TradCuts"] = str(len(inside))
    m["TradInnerCuts"] = str(sum(1 for r in inside if r["level"] != "juz"))
    m["TradJuzCuts"] = str(sum(1 for r in inside if r["level"] == "juz"))
    m["CutDepth"] = f"{st.median(float(r['depth']) for r in inside) * 100:.0f}"
    m["TradLeaning"] = str(sum(int(r["leaning_start"]) for r in rows))

    # balance, traditional and final
    us = rub.ayat()
    c = rub.mix(us)
    final = rub.solve(us)

    def bal(starts):
        h = rub.relative(us, starts[::4], c, 2)
        r = rub.relative(us, starts, c, 4)
        ra = rub.sizes(us, starts, c)
        ha = rub.sizes(us, starts[::4], c)
        return dict(hw=max(map(abs, h)), hcv=st.pstdev(h), rw=max(map(abs, r)), rcv=st.pstdev(r),
                    rr=max(ra) / min(ra), hr=max(ha) / min(ha))
    for name, s in (("Trad", trad), ("New", final.starts)):
        b = bal(s)
        m[f"{name}HizbWorst"] = f"{b['hw'] * 100:.1f}"
        m[f"{name}HizbCV"] = f"{b['hcv'] * 100:.1f}"
        m[f"{name}RubWorst"] = f"{b['rw'] * 100:.1f}"
        m[f"{name}RubCV"] = f"{b['rcv'] * 100:.1f}"
        m[f"{name}RubRatio"] = f"{b['rr']:.2f}"
        m[f"{name}HizbRatio"] = f"{b['hr']:.2f}"
    jz = rub.sizes(us, trad[::8], c)
    mean = sum(jz) / 30
    m["TradJuzWorst"] = f"{max(abs(x / mean - 1) for x in jz) * 100:.1f}"
    sol3 = json.loads((DATA / "juz" / "solution.json").read_text())
    m["OptJuzWorst"] = f"{sol3['max_combined_dev_pct']:.1f}"
    m["NewInnerCuts"] = str(len(final.mid_phrase))

    # review round 1 (hizb)
    rr = reviews.load_splits(ROOT / "reviews" / "2026-10-18-hizb-splits" / "splits.tsv")
    m["HizbCandidates"] = str(sum(1 for r in rr if r["kind"] == "hizb"))
    m["HizbSplits"] = str(sum(1 for r in rr if r["kind"] == "hizb" and r["decision"] == "accept"))
    m["JuzSplits"] = str(sum(1 for r in rr if r["kind"] == "juz" and r["decision"] == "accept"))

    # granularity: targeted splits accepted, then phrase-only re-solve; and the aya-end ceiling
    # review round 2 (quarters)
    r2 = reviews.load_splits(ROOT / "reviews" / "2026-10-21-rub-splits" / "splits.tsv")
    m["RubRoundBoundaries"] = str(len({(r["hizb"], r["boundary"]) for r in r2}))
    m["RubRoundCandidates"] = str(len(r2))
    m["RubRoundSplits"] = str(sum(1 for r in r2 if r["decision"] == "accept"))
    m["RubRoundKept"] = str(int(m["RubRoundBoundaries"]) - int(m["RubRoundSplits"]))
    m["ReviewedRub"] = f"({m['RubRoundSplits']},{float(m['NewRubCV']):.2f})"
    m["ReviewedRubWorst"] = f"({m['RubRoundSplits']},{float(m['NewRubWorst']):.2f})"
    # the curve starts from the phrases before the quarter round (its accepted splits removed)
    idx_ = {(u.sura, u.aya): u.index for u in us}
    round2 = {idx_[tuple(map(int, r["proposed_start"].split(":")))] for r in r2 if r["decision"] == "accept"}
    base = {u.index for u in us if u.phrase_start} - round2

    def with_starts(st_):
        return [dataclasses.replace(u, phrase_start=(u.index in st_)) for u in us]
    u0 = with_starts(base)  # the state before the quarter round
    curve = []
    for pen in (INF, 0.15, 0.10, 0.08, 0.05, 0.04, 0.0):
        add = set() if pen == INF else set(rub.solve(u0, mid_phrase=pen, cap=None, objective="penalized").mid_phrase)
        u2 = with_starts(base | add)
        d = rub.solve(u2)
        r = rub.relative(u2, d.starts, c, 4)
        curve.append((len(add), max(map(abs, r)) * 100, st.pstdev(r) * 100))
    u2 = with_starts({u.index for u in us})
    d = rub.solve(u2)
    r = rub.relative(u2, d.starts, c, 4)
    m["CeilRubWorst"] = f"{max(map(abs, r)) * 100:.1f}"
    m["CeilRubCV"] = f"{st.pstdev(r) * 100:.1f}"
    m["CurveCV"] = "".join(f"({n},{cv:.2f})" for n, _, cv in curve)
    m["CurveWorst"] = "".join(f"({n},{w:.2f})" for n, w, _ in curve)
    m["CurveRows"] = r" \\ ".join(f"{n} & $\\pm${w:.1f}\\% & {cv:.1f}\\%" for n, w, cv in curve)
    knee = min(curve, key=lambda x: abs(x[2] - 2.0 * float(m["CeilRubCV"])) if x[0] else 99)
    m["KneeSplits"], m["KneeWorst"], m["KneeCV"] = str(knee[0]), f"{knee[1]:.1f}", f"{knee[2]:.1f}"

    # counting schools: every boundary must be an aya end agreed by all six systems
    uc = rub.ayat()
    prim = json.loads((DATA / "source" / "counting" / "book-boundary-primitives.json").read_text(encoding="utf-8"))["surahs"]
    m["DisputedEnds"] = str(sum(1 for sv in prim.values() for v in sv.values()
                                if "end" in v and set(v["end"]["counted_by"]) != rub.COUNTING_SYSTEMS))
    tb = [i for i in scores.traditional_starts(1) if i]
    m["TradBoundaries"] = str(len(tb))
    m["TradDisputed"] = str(sum(1 for i in tb if rub.disputed_end(uc[i])))
    cnow = rub.mix(uc)
    dnow = rub.solve(uc)
    m["NewDisputed"] = str(sum(1 for i in dnow.starts if rub.disputed_end(uc[i])))
    keep = rub.disputed_end
    rub.disputed_end = lambda u: []
    try:
        dfree = rub.solve(uc)
    finally:
        rub.disputed_end = keep
    moved = [(uc[x].ref, uc[y].ref) for x, y in zip(dfree.starts, dnow.starts) if x != y]
    m["CountMoved"] = str(len(moved))
    m["CountMovedList"] = ", ".join(f"{x}$\\to${y}" for x, y in moved)
    m["CountFreeRubCV"] = f"{st.pstdev(rub.relative(uc, dfree.starts, cnow, 4)) * 100:.1f}"

    # classical pause grades at every boundary (al-Muktafā, Manār al-Hudā) and Ghayth's quarters
    S = waqf.stops()
    both = [(waqf.RANK[v["muktafa"]], waqf.RANK[v["manar"]]) for v in S.values() if len(v) == 2]
    m["StopsMuktafa"] = f"{sum('muktafa' in v for v in S.values()):,}"
    m["StopsManar"] = f"{sum('manar' in v for v in S.values()):,}"
    m["StopsNear"] = f"{sum(abs(a - b) <= 1 for a, b in both) / len(both) * 100:.0f}"
    for name, starts in (("Trad", [i for i in scores.traditional_starts(1) if i]), ("New", [i for i in dnow.starts if i])):
        c = collections.Counter(waqf.boundary(uc, i)[0] for i in starts)
        n = len(starts)
        m[f"Grade{name}Surah"] = str(c["surah end"])
        m[f"Grade{name}Tamm"] = str(c["تام"])
        m[f"Grade{name}Kafi"] = str(c["كاف"])
        m[f"Grade{name}Weak"] = str(c["حسن"] + c["جائز/صالح"] + c["ليس بوقف"])
        m[f"Grade{name}None"] = str(c["not graded"])
        m[f"Grade{name}Strong"] = f"{(c['surah end'] + c['تام'] + c['كاف']) / n * 100:.0f}"
    qs = waqf.quarters()
    loc = [x for x in qs if x.ghayth_end]
    m["GhaythLocated"] = str(len(loc))
    m["GhaythSame"] = str(sum(x.ghayth_end == x.madina_end for x in loc))
    m["GhaythConsensus"] = str(sum(x.standing == "consensus" for x in loc))
    diff = [x for x in loc if x.ghayth_end != x.madina_end]
    m["GhaythDiff"] = str(len(diff))
    m["GhaythAlt"] = str(sum(waqf.madina_named(x) for x in diff))
    m["GhaythDepart"] = str(len(diff) - int(m["GhaythAlt"]))

    out = ROOT / "paper" / "numbers.tex"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("% Generated by scripts/paper_numbers.py; do not edit by hand.\n")
        for k, v in m.items():
            fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
    print(f"wrote {out}")
    for k, v in m.items():
        print(k, v)


if __name__ == "__main__":
    main()
