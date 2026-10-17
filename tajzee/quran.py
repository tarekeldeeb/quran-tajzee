"""Access to the Tanzil Quran text and surah metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from . import SOURCE_TEXT

SURAH_NAMES = (
    "الفاتحة البقرة آل_عمران النساء المائدة الأنعام الأعراف الأنفال التوبة يونس "
    "هود يوسف الرعد إبراهيم الحجر النحل الإسراء الكهف مريم طه "
    "الأنبياء الحج المؤمنون النور الفرقان الشعراء النمل القصص العنكبوت الروم "
    "لقمان السجدة الأحزاب سبأ فاطر يس الصافات ص الزمر غافر "
    "فصلت الشورى الزخرف الدخان الجاثية الأحقاف محمد الفتح الحجرات ق "
    "الذاريات الطور النجم القمر الرحمن الواقعة الحديد المجادلة الحشر الممتحنة "
    "الصف الجمعة المنافقون التغابن الطلاق التحريم الملك القلم الحاقة المعارج "
    "نوح الجن المزمل المدثر القيامة الإنسان المرسلات النبأ النازعات عبس "
    "التكوير الانفطار المطففين الانشقاق البروج الطارق الأعلى الغاشية الفجر البلد "
    "الشمس الليل الضحى الشرح التين العلق القدر البينة الزلزلة العاديات "
    "القارعة التكاثر العصر الهمزة الفيل قريش الماعون الكوثر الكافرون النصر "
    "المسد الإخلاص الفلق الناس"
).split()
SURAH_NAMES = {i + 1: n.replace("_", " ") for i, n in enumerate(SURAH_NAMES)}
assert len(SURAH_NAMES) == 114

# Harakat, Quranic annotation marks and tatweel; used for compact, searchable text.
_DIACRITICS = re.compile("[ً-ٰٟۖ-ۭـ]")


@dataclass(frozen=True)
class Aya:
    sura: int
    aya: int
    text: str

    @property
    def ref(self) -> str:
        return f"{self.sura}:{self.aya}"


class Quran:
    """The full text, indexed by (sura, aya)."""

    def __init__(self, ayat: list[Aya]):
        self.ayat = ayat
        self._by_ref = {(a.sura, a.aya): a for a in ayat}
        self.counts: dict[int, int] = {}
        for a in ayat:
            self.counts[a.sura] = max(self.counts.get(a.sura, 0), a.aya)

    def __len__(self) -> int:
        return len(self.ayat)

    def __getitem__(self, ref: tuple[int, int]) -> Aya:
        return self._by_ref[ref]

    def __contains__(self, ref: tuple[int, int]) -> bool:
        return ref in self._by_ref

    def surah(self, sura: int) -> list[Aya]:
        return [self[(sura, a)] for a in range(1, self.counts[sura] + 1)]

    def range(self, sura: int, first: int, last: int) -> list[Aya]:
        return [self[(sura, a)] for a in range(first, last + 1)]


def plain(text: str) -> str:
    """Strip diacritics and map alef wasla to alef: compact text for reading and search."""
    return _DIACRITICS.sub("", text).replace("ٱ", "ا")


@lru_cache(maxsize=None)
def load(path: Path | str = SOURCE_TEXT) -> Quran:
    """Load a Tanzil ``sura|aya|text`` file, skipping its ``#`` licence header."""
    ayat = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            sura, aya, text = line.rstrip("\n").split("|", 2)
            ayat.append(Aya(int(sura), int(aya), text))
    return Quran(ayat)
