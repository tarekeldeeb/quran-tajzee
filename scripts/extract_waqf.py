#!/usr/bin/env python3
"""Build data/source/waqf/ from the OpenITI texts of three classical works on pauses.

    python scripts/extract_waqf.py [--texts DIR]

Downloads the texts (pinned OpenITI commits) into build/openiti/ unless --texts points to them,
then writes:

    stops.tsv            sura, aya, the grade al-Muktafā and Manār al-Hudā give the aya end
    ghayth-quarters.tsv  al-Ṣafāqusī's note on the last word of each of the 240 quarters

Only grades and short quotes of the authors' notes are kept, not the texts.
"""

import argparse
import collections
import csv
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tajzee import quran, scores, waqf  # noqa: E402

RAW = "https://raw.githubusercontent.com/OpenITI"
TEXTS = {
    "muktafa": ("0450AH", "8b80029191e1b7a8809d812ec6186df862e18217",
                "0444AbuCamrDani/0444AbuCamrDani.MuktafiFiWaqf/0444AbuCamrDani.MuktafiFiWaqf.Shamela0026461-ara1"),
    "manar": ("1100AH", "aef851961abf65f7cc4986a0fb420179d60f81c4",
              "1100IbnCabdKarimAshmuniMisri/1100IbnCabdKarimAshmuniMisri.ManarHuda/"
              "1100IbnCabdKarimAshmuniMisri.ManarHuda.Shamela0006496-ara1"),
    "ghayth": ("1125AH", "fd85c92138663f09924b9a0323f674614394e4c1",
               "1118IbnMuhammadNuriSafaqsi/1118IbnMuhammadNuriSafaqsi.GhaythNafc/"
               "1118IbnMuhammadNuriSafaqsi.GhaythNafc.Shamela0027083-ara1"),
}

q = quran.load()
LEN = collections.Counter(a.sura for a in q.ayat)
AW = {(a.sura, a.aya): waqf.skeleton(a.text).split() for a in q.ayat}


def text(name: str, folder: Path) -> str:
    repo, commit, path = TEXTS[name]
    f = folder / f"{name}.txt"
    if not f.exists():
        folder.mkdir(parents=True, exist_ok=True)
        url = f"{RAW}/{repo}/{commit}/data/{path}"
        print(f"downloading {url}")
        f.write_bytes(urllib.request.urlopen(url).read())
    s = f.read_text(encoding="utf-8")
    s = re.sub(r"~~|PageV\d+P\d+|ms\d+|</?span>", " ", s)
    return re.sub(r"\s+", " ", s)


def ends_with(sura: int, aya: int, quote: str, k: int) -> bool:
    w = waqf.skeleton(quote).split()
    aw = AW.get((sura, aya))
    return bool(w and aw) and aw[-min(k, len(w)):] == w[-min(k, len(w)):]


def manar(s: str) -> dict:
    """Manār tags each aya-end quote with its number: {… (80)} [80] كاف. Surahs follow in order."""
    out, also = {}, {}
    start = s.find("# سورة الفاتحة")
    cur = 1
    for m in re.finditer(r"\{([^{}]*?)(?:\((\d+)\))?\}\s*\[(\d+)\]", s):
        if m.start() < start:
            continue
        n, quote = int(m.group(3)), m.group(1)
        g = waqf.grade(s[m.end():m.end() + 100])
        if m.group(2):          # an aya end, numbered
            sura = next((x for x in range(cur, min(cur + 4, 115)) if ends_with(x, n, quote, 1)), None)
            if sura is None:
                continue
            cur = sura
            if g:
                out.setdefault((sura, n), g)
        if not g:
            continue
        # «… كاف، ومثله «X»، وكذا «Y» و«Z»»: further aya ends, same grade, not numbered
        tail = s[m.end():m.end() + 300].split("#")[0]
        cut = re.search(r"[؛.]", tail)
        tail = tail[:cut.start()] if cut else tail
        if not re.search("مثله|كذا", tail):
            continue
        pos = cur and n
        for x in re.findall(r"«([^«»]+)»", tail[tail.find("مثله") if "مثله" in tail else tail.find("كذا"):]):
            w = waqf.skeleton(x).split()
            if not w:
                continue
            k = min(len(w), 3)
            hit = next((a for a in range(pos, min(pos + 25, LEN[cur] + 1)) if AW[(cur, a)][-k:] == w[-k:]), None)
            if hit:
                also.setdefault((cur, hit), g)
                pos = hit
    for k, g in also.items():
        out.setdefault(k, g)
    return out


def muktafa(s: str) -> dict:
    """al-Muktafā quotes {words} or ((words)) then a grade, in text order, without aya numbers.
    Each quote is matched to the next aya that ends with the same words, inside its surah."""
    heads = [m.start() for m in re.finditer(r"#+ (?:\| )*سورة [^#]{1,30}", s)]
    nums = list(range(2, 63)) + list(range(64, 115))  # al-Munāfiqūn has no heading in this edition
    assert len(heads) == len(nums), len(heads)
    fat = s.rfind("#", 0, s.rfind("الفاتحة", 0, heads[0]))
    segs = [(1, fat, heads[0])] + [(nums[i], heads[i], heads[i + 1] if i + 1 < len(heads) else len(s))
                                   for i in range(len(heads))]
    out = {}
    for sura, a, b in segs:
        seg, cur, last = s[a:b], 1, None
        for m in re.finditer(r"\{([^{}]*)\}|\(\(([^()]*)\)\)", seg):
            quote = m.group(1) or m.group(2) or ""
            w = waqf.skeleton(quote).split()
            if not w:
                continue
            g = waqf.grade(seg[m.end():m.end() + 80])
            if g is None and "مثله" in seg[max(0, m.start() - 12):m.start()]:
                g = last           # «ومثله {…}»: the same grade as the one before
            if g:
                last = g
            k = min(len(w), 3)
            hit = next((x for x in range(cur, min(cur + (12 if k == 1 else 40), LEN[sura] + 1))
                        if AW[(sura, x)][-k:] == w[-k:]), None)
            if hit is None:
                continue
            cur = hit
            if g:
                out.setdefault((sura, hit), g)
    return out


GR = re.compile(r"(تام|كاف|حسن|صالح|وقف للجميع|آخر السورة)")
END = ("منتهى", "ختام", "ونصف الحزب", "تمام الربع", "تمام النصف", "تمام نصف", "تمام الحزب", "انتهاء")


def ghayth(s: str) -> list[dict]:
    """Each quarter of Ghayth closes with a note on its last word («… تام وفاصلة ومنتهى الربع
    بإجماع») just before the quarter's imāla section (الممال). Locate the word near the Madina
    quarter end, in order."""
    marks = [m.start() for m in re.finditer(r"### \| (?:### \| )*الممال", s)]
    seq = q.ayat
    tr = scores.traditional_starts(1)
    end_i = [i - 1 for i in tr[1:]] + [len(seq) - 1]

    def same(a, b):
        return a == b or a.lstrip("وف") == b.lstrip("وف")

    notes, prev = [], 0
    for h in marks:
        seg, prev = s[prev:h], h
        p1 = max(seg.rfind(x) for x in END if x != "ختام")
        p2 = seg.rfind("ختام")
        pos = p1 if p1 >= 0 and (p2 < 0 or p2 - p1 < 120) else p2   # «… ومنتهى الربع … والشاذ ختام السورة»
        if pos < 0:
            continue
        heads = []
        star = seg.rfind("*", max(0, pos - 220), pos)
        if star >= 0:
            heads.append(seg[max(0, star - 40):star])
        mk = list(re.finditer(r"\d+ - # ", seg[:pos]))
        if mk:
            e = seg[mk[-1].end():pos]
            g, st = GR.search(e), e.find("*")
            heads.append(e[:min([x for x in (st, g.start() if g else -1) if x >= 0] or [40])])
        w0 = seg[max(0, pos - 160):pos]
        gs = [g for g in GR.finditer(w0) if "*" not in w0[g.end():] and "." not in w0[g.end():]]
        if gs:
            pre = re.sub(r"(وهو|فهو|وهي)\s*$", "", w0[:gs[0].start()].strip(" ،,"))
            heads.append(" ".join(pre.split()[-2:]))
        clause = seg[pos:pos + 400]
        stop = min([i for i in (clause.find("."), clause.find("###")) if i > 0] or [len(clause)])
        lead = w0[gs[0].start():] if gs else ""
        notes.append(([re.sub(r"\(\d+\)", "", x) for x in heads], lead, clause[:stop].strip()))

    rows, j = [], 0
    for heads, lead, clause in notes:
        best = None
        for head in heads:
            w = waqf.skeleton(head).split()
            if not w:
                continue
            for jj in range(j, min(j + 4, 240)):
                for d in range(-10, 11):
                    i = end_i[jj] + d
                    if 0 <= i < len(seq) and same(AW[(seq[i].sura, seq[i].aya)][-1], w[-1]):
                        key = (jj - j, abs(d))
                        if best is None or key < best[0]:
                            best = (key, jj, i)
        if best is None:
            continue
        _, jj, i = best
        g = waqf.grade(lead, 40) or ""
        rows.append({"quarter": jj + 1, "madina_end": seq[end_i[jj]].ref, "ghayth_end": seq[i].ref,
                     "grade": g, "standing": waqf.standing(clause),
                     "note": re.sub(r"\s+", " ", re.sub(r" و$", " و", lead.rstrip()) + ("" if lead.rstrip().endswith(" و") else " ") + clause).replace("*", "").strip()})
        j = jj + 1
    got = {r["quarter"] for r in rows}
    rows += [{"quarter": n + 1, "madina_end": seq[end_i[n]].ref, "ghayth_end": "", "grade": "",
              "standing": "", "note": ""} for n in range(240) if n + 1 not in got]
    return sorted(rows, key=lambda r: r["quarter"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--texts", type=Path, default=ROOT / "build" / "openiti")
    a = ap.parse_args()
    mk, mn = muktafa(text("muktafa", a.texts)), manar(text("manar", a.texts))
    waqf.WAQF.mkdir(parents=True, exist_ok=True)
    with open(waqf.WAQF / "stops.tsv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["sura", "aya", "muktafa", "manar"])
        for u in q.ayat:
            k = (u.sura, u.aya)
            if k in mk or k in mn:
                w.writerow([u.sura, u.aya, mk.get(k, ""), mn.get(k, "")])
    rows = ghayth(text("ghayth", a.texts))
    with open(waqf.WAQF / "ghayth-quarters.tsv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    located = sum(1 for r in rows if r["ghayth_end"])
    agree = sum(1 for r in rows if r["ghayth_end"] == r["madina_end"])
    print(f"al-Muktafā: {len(mk)} aya ends graded; Manār al-Hudā: {len(mn)}; both: {len(mk.keys() & mn.keys())}")
    print(f"Ghayth: {located} of 240 quarter ends located, {agree} at the Madina end")


if __name__ == "__main__":
    main()
