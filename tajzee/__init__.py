"""Quran-Tajzee: balanced, meaningful Juz definitions derived from the Tanzil text.

The package holds the shared building blocks every task uses:

- ``tajzee.quran``   – load the Tanzil text and surah metadata
- ``tajzee.phrases`` – load, validate and save the subject-phrase segmentation
- ``tajzee.reviews`` – apply review marks (approve / merge / split / topic) to phrases
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SOURCE_TEXT = DATA / "source" / "quran-uthmani.txt"
PHRASES_TSV = DATA / "phrases" / "phrases.tsv"

MAX_PHRASE_AYAT = 10

__all__ = ["ROOT", "DATA", "SOURCE_TEXT", "PHRASES_TSV", "MAX_PHRASE_AYAT"]
