#!/usr/bin/env python3
"""Analyse the balanced juz; writes docs/tasks/03-juz-analysis.md and data/juz/analysis.json.

    python scripts/analyze_juz.py

Compares the solved division with the traditional juz on the same size model (surah
openings included), sweeps the recitation/typesetting weight and the objective, shows
where the new boundaries fall relative to the traditional ones, and explains the
worst-balanced juz.
"""

import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tajzee import DATA, juz, quran, scores  # noqa: E402

OUT = ROOT / "docs" / "tasks" / "03-juz-analysis.md"
JSON_OUT = DATA / "juz" / "analysis.json"
WEIGHT = 0.5
BP, CAP = juz.BREAK_PENALTY, juz.CAP


def solve(us, w=WEIGHT, **kw):
    """The default division: 50/50 mix with the surah-break penalty and cap."""
    if kw.get("objective") not in (None, "penalized"):
        return juz.solve(us, w, **kw)
    kw.pop("objective", None)
    return juz.solve(us, w, break_penalty=kw.pop("break_penalty", BP), cap=kw.pop("cap", CAP), **kw)


def stats(xs):
    m = st.fmean(xs)
    return dict(mean=m, cv=st.pstdev(xs) / m, min=min(xs), max=max(xs), max_min=max(xs) / min(xs),
                max_abs_dev=max(abs(x / m - 1) for x in xs))


def measure(groups_rec, groups_px, w):
    R, P = st.fmean(groups_rec), st.fmean(groups_px)
    comb = [w * r / R + (1 - w) * p / P for r, p in zip(groups_rec, groups_px)]
    return dict(recitation=stats(groups_rec), typeset_px=stats(groups_px), combined=stats(comb))


def table(rows, header):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    return "\n".join(out + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def main() -> None:
    q = quran.load()
    flat = [(a.sura, a.aya) for a in q.ayat]
    gidx = {r: i for i, r in enumerate(flat)}
    us = juz.units()
    k = scores.constants()
    line_px = juz.LINE_EM * k.font_px
    hw = juz.HEADER_WEIGHT

    # per-aya sizes with surah openings, for divisions that do not follow phrases
    ay = scores.ayat()
    a_rec, a_px = [], []
    for s, a in flat:
        r, p = float(ay[(s, a)].recitation), ay[(s, a)].typeset_px + (k.space_px if a > 1 else 0.0)
        if a == 1:
            r += k.basmala_recitation if scores.opens_with_basmala(s) else 0
            p += juz.header_lines(s) * line_px * hw
        a_rec.append(r)
        a_px.append(p)

    def by_starts(starts):
        b = list(starts) + [len(flat)]
        return ([sum(a_rec[x:y]) for x, y in zip(b, b[1:])], [sum(a_px[x:y]) for x, y in zip(b, b[1:])])

    sol = solve(us)
    new_starts = [gidx[(p[0].sura, p[0].first)] for p in sol.parts]
    trad_starts = scores.traditional_starts(8)
    R = {}
    nr, npx = by_starts(new_starts)
    tr, tpx = by_starts(trad_starts)
    R["new"] = measure(nr, npx, WEIGHT)
    R["traditional"] = measure(tr, tpx, WEIGHT)

    # weight sweep and objectives
    sweep = []
    for w in (0.0, 0.25, 0.5, 0.75, 1.0):
        s = solve(us, w)
        r_, p_ = by_starts([gidx[(p[0].sura, p[0].first)] for p in s.parts])
        m = measure(r_, p_, WEIGHT)
        sweep.append(dict(weight=w, rec_cv=m["recitation"]["cv"], rec_dev=m["recitation"]["max_abs_dev"],
                          px_cv=m["typeset_px"]["cv"], px_dev=m["typeset_px"]["max_abs_dev"],
                          comb_dev=m["combined"]["max_abs_dev"]))
    R["weight_sweep"] = sweep
    objs = []
    for o in ("penalized", "minimax+lsq", "lsq", "minimax", "each"):
        s = solve(us, objective=o)
        r_, p_ = by_starts([gidx[(p[0].sura, p[0].first)] for p in s.parts])
        m = measure(r_, p_, WEIGHT)
        objs.append(dict(objective=o, cv=m["combined"]["cv"], max_dev=m["combined"]["max_abs_dev"],
                         rec_dev=m["recitation"]["max_abs_dev"], px_dev=m["typeset_px"]["max_abs_dev"],
                         breaks=s.surah_breaks))
    R["objectives"] = objs

    # surah-break penalty sweep (with the cap, and without)
    pen = []
    for p_ in (0.0, 0.02, 0.03, 0.035, 0.04, 0.045, 0.05, 0.07, 0.10):
        for cap in (CAP, None):
            s = juz.solve(us, WEIGHT, objective="lsq") if p_ == 0 else juz.solve(us, WEIGHT, break_penalty=p_, cap=cap)
            r_, x_ = by_starts([gidx[(g[0].sura, g[0].first)] for g in s.parts])
            m = measure(r_, x_, WEIGHT)
            pen.append(dict(penalty=p_, cap=cap if p_ else None, breaks=s.surah_breaks, cv=m["combined"]["cv"],
                            max_dev=m["combined"]["max_abs_dev"]))
            if p_ == 0:
                break
    R["penalty_sweep"] = pen
    trad_breaks = sum(1 for i in scores.traditional_starts(8)[1:] if flat[i][1] != 1)

    hdr = []
    for h in (0.0, 0.5, 1.0):
        uh = juz.units(header_weight=h)
        s = solve(uh)
        Rr = sum(u.recitation for u in uh) / 30
        Pp = sum(u.typeset_px for u in uh) / 30
        d = [(sum(u.recitation for u in g) / Rr - 1, sum(u.typeset_px for u in g) / Pp - 1) for g in s.parts]
        hdr.append(dict(header_weight=h, rec_dev=max(abs(a) for a, _ in d), px_dev=max(abs(b) for _, b in d),
                        comb_dev=max(abs(a + b) / 2 for a, b in d), last_start=f"{s.parts[-1][0].sura}:{s.parts[-1][0].first}",
                        last=d[-1]))
    R["header_sensitivity"] = hdr

    # boundaries
    shifts = []
    for n in range(1, 30):
        a, b = trad_starts[n], new_starts[n]
        lo, hi = min(a, b), max(a, b)
        between = (sum(a_rec[lo:hi]) / st.fmean(nr) * WEIGHT + sum(a_px[lo:hi]) / st.fmean(npx) * (1 - WEIGHT))
        shifts.append(dict(juz=n + 1, traditional=f"{flat[a][0]}:{flat[a][1]}", new=f"{flat[b][0]}:{flat[b][1]}",
                           ayat=b - a, share=(1 if b >= a else -1) * between))
    R["boundary_shifts"] = shifts
    R["surah_starts"] = dict(new=sum(1 for i in new_starts if flat[i][1] == 1),
                             traditional=sum(1 for i in trad_starts if flat[i][1] == 1))
    R["surah_breaks"] = dict(new=sol.surah_breaks, traditional=trad_breaks)
    R["same_start"] = sum(1 for a, b in zip(trad_starts, new_starts) if a == b)
    R["phrases_per_juz"] = [len(p) for p in sol.parts]
    JSON_OUT.write_text(json.dumps(R, ensure_ascii=False, indent=1) + "\n")

    # ------------------------------------------------------------- markdown
    L = []
    w = L.append
    w("# Task 3 — Balanced juz: analysis\n")
    w("_Generated by `scripts/analyze_juz.py`; do not edit by hand._\n")
    w("Division: `data/juz/juz.tsv`, solved by `scripts/solve_juz.py` with a 50/50 mix of "
      f"recitation and typesetting and a surah-break penalty (p = {BP * 100:g}%, every juz within "
      f"±{CAP * 100:g}%); see [03-balanced-juz.md](03-balanced-juz.md). The traditional juz are "
      "measured on the same model: per-aya scores plus the basmala of each surah opening.\n")

    w("## 1. Balance: new against traditional\n")
    rows = []
    for key, label in (("recitation", "Recitation"), ("typeset_px", "Typesetting"), ("combined", "Combined 50/50")):
        for name in ("traditional", "new"):
            d = R[name][key]
            rows.append([label, name, f"{d['cv']:.4f}", f"{d['max_min']:.3f}×", f"±{d['max_abs_dev'] * 100:.1f}%"])
    w(table(rows, ["score", "division", "CV", "longest/shortest", "worst deviation"]))
    t, n = R["traditional"], R["new"]
    w(f"\nOn the combined score the spread (CV) falls from {t['combined']['cv']:.4f} to "
      f"{n['combined']['cv']:.4f}, {t['combined']['cv'] / n['combined']['cv']:.1f}× more even, and the "
      f"longest juz is {n['combined']['max_min']:.3f}× the shortest instead of {t['combined']['max_min']:.3f}×.")
    for key, label in (("recitation", "Recitation"), ("typeset_px", "Typesetting")):
        a, b = t[key], n[key]
        verdict = "improves on every measure" if (b["cv"] < a["cv"] and b["max_abs_dev"] < a["max_abs_dev"]) \
            else ("has a lower spread but a larger worst case" if b["cv"] < a["cv"] else "is less even")
        w(f"{label} alone {verdict}: CV {a['cv']:.4f} → {b['cv']:.4f}, worst ±{a['max_abs_dev'] * 100:.1f}% → "
          f"±{b['max_abs_dev'] * 100:.1f}%.")
    w("")

    w("## 2. The 30 juz\n")
    rows = []
    for i, part in enumerate(sol.parts):
        a = part[0]
        rows.append([i + 1, f"{a.sura}:{a.first}", quran.SURAH_NAMES[a.sura], f"{part[-1].sura}:{part[-1].last}",
                     len(part), sum(u.ayat for u in part), f"{nr[i] / st.fmean(nr) * 100 - 100:+.1f}%",
                     f"{npx[i] / st.fmean(npx) * 100 - 100:+.1f}%", a.topic])
    w(table(rows, ["juz", "starts", "surah", "ends", "phrases", "ayat", "recitation", "typesetting", "opens with"]))
    w("\nDeviations are from the mean of each score over the 30 juz.\n")

    w("## 3. Weight between recitation and typesetting\n")
    w("The same solver at other weights; every row is measured on both scores and on the 50/50 mix.\n")
    rows = [[f"{x['weight']:.2f}", f"{x['rec_cv']:.4f}", f"±{x['rec_dev'] * 100:.1f}%", f"{x['px_cv']:.4f}",
             f"±{x['px_dev'] * 100:.1f}%", f"±{x['comb_dev'] * 100:.1f}%"] for x in sweep]
    w(table(rows, ["weight (recitation)", "recitation CV", "recitation worst", "typesetting CV",
                   "typesetting worst", "50/50 worst"]))
    s0, s1 = sweep[0], sweep[-1]
    w(f"\nBalancing one score alone leaves the other at CV {s0['rec_cv']:.3f} (recitation, weight 0) or "
      f"{s1['px_cv']:.3f} (typesetting, weight 1). The 50/50 mix keeps both near the middle of that range.\n")

    w("## 4. Surah breaks\n")
    w("A juz that starts in the middle of a surah is penalised: it costs as much as a juz off its "
      "target by p. The solver minimises Σ((S−T)/T)² + p²·B, with B the number of juz starting "
      "mid-surah, optionally with every juz held within a cap.\n")
    rows = [[f"{x['penalty'] * 100:g}%", "none" if x["cap"] is None else f"±{x['cap'] * 100:g}%",
             x["breaks"], 30 - x["breaks"], f"{x['cv']:.4f}", f"±{x['max_dev'] * 100:.1f}%"] for x in pen]
    w(table(rows, ["penalty p", "cap", "juz starting mid-surah", "juz opening a surah", "combined CV",
                   "combined worst"]))
    w(f"\nThe traditional juz: {trad_breaks} start mid-surah. Up to p = 2% the penalty changes nothing: "
      "no surah start lies close enough to a balanced cut to be worth it. At 3% the first cuts move to "
      "surah starts, and at 3.5% four more follow for only +0.2% in the worst juz. That result then "
      "holds through 4.5%, and the default p = 4% sits in the middle of it. At 5% two more juz open a "
      "surah, but the worst juz jumps to the ±5% cap, or to ±6.2% without it. Beyond that only the "
      "cap holds the balance.\n")

    w("## 5. Objective\n")
    rows = [[x["objective"] + (" (default)" if x["objective"] == "penalized" else ""), x["breaks"],
             f"{x['cv']:.4f}", f"±{x['max_dev'] * 100:.2f}%", f"±{x['rec_dev'] * 100:.1f}%",
             f"±{x['px_dev'] * 100:.1f}%"] for x in objs]
    w(table(rows, ["objective", "mid-surah starts", "combined CV", "combined worst", "recitation worst",
                   "typesetting worst"]))
    w(f"\n- `penalized` (default): least squares plus the surah-break penalty, p = {BP * 100:g}%, cap ±{CAP * 100:g}%.")
    w("- `minimax`: the smallest possible worst juz on the mix; the other juz are left loose.")
    w("- `lsq`: the smallest sum of squared deviations on the mix.")
    w("- `minimax+lsq`: least squares among the divisions that reach the minimax worst case.")
    w("- `each`: no mixing; the smallest worst deviation of *either* score in any juz, then least squares.\n")

    w("## 6. Surah header lines in the typesetting score\n")
    w("Task 2 measures the text's own width. A printed Mushaf also gives each surah a header "
      "(title line, and a basmala line for most surahs). Counting those lines at weight h:\n")
    rows = [[f"{x['header_weight']:.1f}", f"±{x['rec_dev'] * 100:.1f}%", f"±{x['px_dev'] * 100:.1f}%",
             f"±{x['comb_dev'] * 100:.1f}%", x["last_start"],
             f"{x['last'][0] * 100:+.1f}% / {x['last'][1] * 100:+.1f}%"] for x in hdr]
    w(table(rows, ["header weight", "recitation worst", "typesetting worst", "50/50 worst", "juz 30 starts",
                   "juz 30 recitation / print"]))
    w("\nJuz ʿAmma holds 37 of the 114 headers. Counted in full, they make the last juz long in print "
      "and short in recitation in a fixed ratio, wherever it starts; no division can bring both "
      "within a few percent. The default here is the Task 2 definition (weight 0). A typeset Mushaf "
      "can absorb the headers the way Quran-Nazm does, by giving juz 30 extra pages.\n")

    w("## 7. Where the new juz start\n")
    w(f"{R['same_start']} of the 29 inner boundaries coincide with a traditional juz start; "
      f"{R['surah_starts']['new']} new juz open a surah (traditional: {R['surah_starts']['traditional']}).\n")
    rows = [[x["juz"], x["traditional"], x["new"], f"{x['ayat']:+d}", f"{x['share'] * 100:+.0f}%"] for x in shifts]
    w(table(rows, ["juz", "traditional start", "new start", "shift (ayat)", "shift (% of a juz)"]))
    sh = [x["share"] for x in shifts]
    peak = max(shifts, key=lambda x: abs(x["share"]))
    later = sum(1 for x in sh if x > 0)
    earlier = sum(1 for x in sh if x < 0)
    w(f"\n{later} new starts fall after the traditional one and {earlier} before; the median shift is "
      f"{st.median(abs(x) for x in sh) * 100:.0f}% of a juz, the largest {abs(peak['share']) * 100:.0f}% "
      f"(juz {peak['juz']}). Shifts accumulate: whenever traditional juz run shorter than average, every "
      "later boundary moves the same way until longer ones give the difference back.\n")

    w("## 8. The worst juz\n")
    cmb = [nr[i] / st.fmean(nr) * WEIGHT + npx[i] / st.fmean(npx) * (1 - WEIGHT) - 1 for i in range(30)]
    worst = max(range(30), key=lambda i: abs(cmb[i]))
    c = juz.combined(us, WEIGHT)
    plain = juz.solve(us, WEIGHT)
    w(f"Juz {worst + 1} deviates most ({cmb[worst] * 100:+.2f}% on the mix), the price of opening "
      f"{30 - sol.surah_breaks} juz on a surah. Without the penalty the exact limit is "
      f"±{plain.max_dev * 30 * 100:.2f}%, set by phrase granularity: cuts fall only between phrases, and "
      f"the largest phrase is {max(c) * 30 * 100:.1f}% of a juz.\n")

    w("## 9. Takeaways\n")
    w(f"- At 50/50 the new juz are {t['combined']['cv'] / n['combined']['cv']:.1f}× more even than the "
      f"traditional ones on the combined score (worst ±{n['combined']['max_abs_dev'] * 100:.1f}% against "
      f"±{t['combined']['max_abs_dev'] * 100:.1f}%).")
    w(f"- Every juz opens at the start of a subject phrase; {R['surah_starts']['new']} open a surah, "
      f"against {R['surah_starts']['traditional']} traditionally.")
    w("- The result is exactly optimal for the current phrase list and objective, and stays so after each "
      "review round by re-running the solver.")
    w("- Open decisions: the surah-break penalty (section 4) and whether printed surah headers count "
      "(section 6).")
    w("- Next (Task 4): hizb and quarters inside each juz with the same solver, and a review page for the "
      "juz boundaries.")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT} and {JSON_OUT}")


if __name__ == "__main__":
    main()
