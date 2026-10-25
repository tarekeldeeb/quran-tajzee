"""Pause grades (waqf) from three classical works, at aya ends.

- al-Dānī (d. 444), *al-Muktafā fī al-Waqf wa-l-Ibtidāʾ*
- al-Ushmūnī (d. c. 1100), *Manār al-Hudā fī Bayān al-Waqf wa-l-Ibtidāʾ*
- al-Ṣafāqusī (d. 1118), *Ghayth al-Nafʿ*: his note on the last word of each quarter

`scripts/extract_waqf.py` builds the tables in `data/source/waqf/` from the OpenITI texts.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from functools import lru_cache

from . import DATA

WAQF = DATA / "source" / "waqf"

# grade words, as the books use them, and a rank (higher = a stronger stop)
GRADES = (
    ("ليس بوقف", 0), ("ليسا بوقف", 0), ("لا يوقف", 0), ("لا وقف", 0), ("قبيح", 0),
    ("تام", 4), ("أكفى", 3), ("كاف", 3), ("حسن", 2), ("صالح", 1), ("جائز", 1), ("مفهوم", 1),
)
RANK = dict(GRADES)
NAMES = {4: "tamm", 3: "kafi", 2: "hasan", 1: "salih", 0: "none"}

_DI = re.compile("[ً-ٰٟۖ-ۭـ]")


def skeleton(text: str) -> str:
    """Consonant skeleton for matching quotes against the Uthmani text: no vowels, no
    long-vowel letters or hamza seats, ta marbuta as ha."""
    t = _DI.sub("", text).replace("ٱ", "ا")
    t = re.sub("[^ء-ي ]", " ", t)
    t = re.sub("[اويىءأإآؤئ]", "", t).replace("ة", "ه")
    return re.sub(r"\s+", " ", t).strip()


def grade(after: str, window: int = 60) -> str | None:
    """The first grade word in `after` (the text following a quote), if within `window`."""
    if re.match(r"\s*[،,]?\s*نام[،,. ]", after):   # a typo of the edition for «تام» (e.g. 25:20)
        return "تام"
    m = _GRADE_RE.search(after[:window])
    return m.group(1) if m else None


# a grade word on its own (not inside كافرين، تمام …), optionally with a و/ف prefix
_GRADE_RE = re.compile(r"(?<![ء-ي])[وف]?(" + "|".join(w for w, _ in GRADES) + r")(?![ء-ي])")


# how widely a quarter end is accepted, from Ghayth's wording after «منتهى الربع …»
_MAIN = re.compile(r"،? وقيل|،? وعند|،? ول(?=بعض|جماعة)|،? وقال|،? وشذ")


def standing(clause: str) -> str:
    """consensus (بإجماع، بلا خلاف), well-known (المشهور، للجمهور، للأكثر, or his own choice
    عليه عملنا), regional (one of the Maghāriba or the Mashāriqa), or some (عند بعض، جماعة)."""
    main = _MAIN.split(clause)[0]
    if re.search("إجماع|اتفاق|خلاف", main):
        return "consensus"
    if re.search("مغارب|مشارق|المغرب|المشرق|الغرب", main) and "جمهور" not in main and "جميع" not in main:
        return "regional"
    if re.search("مشهور|أكثر|جمهور|الأصح|المختار|اخترناه|عملنا|اللطائف|اقتصر|جرى|جميع", main):
        return "well-known"
    if re.search("بعض|جماعة|قوم|كثير|آخرين", main):
        return "some"
    return "stated"


@dataclass(frozen=True)
class Quarter:
    n: int              # 1..240
    madina_end: str     # sura:aya, the aya before the Madina quarter start
    ghayth_end: str     # sura:aya Ghayth names, or '' if not located
    grade: str          # his grade of the last word (first one named)
    standing: str       # consensus / well-known / some / stated
    note: str           # his note, from the quarter word to the end of the sentence


@lru_cache(maxsize=None)
def stops() -> dict[tuple[int, int], dict[str, str]]:
    """{(sura, aya): {'muktafa': grade, 'manar': grade}} for the aya ends the books grade."""
    out: dict[tuple[int, int], dict[str, str]] = {}
    with open(WAQF / "stops.tsv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            out[(int(r["sura"]), int(r["aya"]))] = {k: r[k] for k in ("muktafa", "manar") if r[k]}
    return out


@lru_cache(maxsize=None)
def quarters() -> list[Quarter]:
    with open(WAQF / "ghayth-quarters.tsv", encoding="utf-8") as fh:
        return [Quarter(int(r["quarter"]), r["madina_end"], r["ghayth_end"], r["grade"], r["standing"],
                        r["note"]) for r in csv.DictReader(fh, delimiter="\t")]


def rank(g: str | None) -> int | None:
    return RANK.get(g) if g else None


def best(sura: int, aya: int) -> int | None:
    """The strongest grade either book gives the end of this aya (None if neither grades it)."""
    g = stops().get((sura, aya), {})
    rs = [RANK[x] for x in g.values() if x in RANK]
    return max(rs) if rs else None


LABEL = {4: "تام", 3: "كاف", 2: "حسن", 1: "جائز/صالح", 0: "ليس بوقف"}
CLASSES = ("surah end", "تام", "كاف", "حسن", "جائز/صالح", "ليس بوقف", "not graded")


def boundary(us, i: int) -> tuple[str, str, str]:
    """(class, al-Muktafā grade, Manār grade) of the aya end before boundary `i` of the aya list
    `us`. A boundary at a surah opening is a surah end, a complete stop by convention."""
    e = us[i - 1]
    g = stops().get((e.sura, e.aya), {})
    mk, mn = g.get("muktafa", ""), g.get("manar", "")
    if us[i].aya == 1:
        return "surah end", mk, mn
    b = best(e.sura, e.aya)
    return (LABEL[b] if b is not None else "not graded"), mk, mn


def madina_named(qr: Quarter) -> bool:
    """Whether al-Ṣafāqusī's note on a quarter names the Madina end among the alternatives
    («… قبله»، «… بعده»، «آخر السورة») where his own end differs from it."""
    from . import quran
    ayat = {a.ref: a for a in quran.load().ayat}
    e = ayat[qr.madina_end]
    last = skeleton(e.text).split()[-1].lstrip("وف")
    note = [x.lstrip("وف") for x in skeleton(qr.note).split()]
    last_of_surah = e.aya == max(a.aya for a in ayat.values() if a.sura == e.sura)
    return last in note or (last_of_surah and "خر" in note)
