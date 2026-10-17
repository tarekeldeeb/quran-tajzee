# Roadmap

Quran-Tajzee derives new Juz definitions that are **balanced** in length for reciters and
typesetters while **starting only at meaningful points** in the text.

Each task gets a document in `docs/tasks/NN-name.md`, its data under `data/<name>/`, its
code in `tajzee/` (library) and `scripts/` (command-line entry points), and tests in `tests/`.

| # | Task | Output | Status |
|---|------|--------|--------|
| 1 | [Subject phrases](tasks/01-phrase-segmentation.md): split the text into 1–10 aya phrases by subject | `data/phrases/phrases.tsv` | draft done, in review |
| 2 | Length measures: size of each phrase in words, letters, and printed lines | per-phrase metrics | next |
| 3 | Balanced Juz: group consecutive phrases into 30 parts of near-equal length | `data/juz/` | planned |
| 4 | Finer divisions: Hizb and quarters inside the new Juz, by the same rules | `data/juz/` | planned |
| 5 | Comparison: the new divisions against the traditional ones | report | planned |

Tasks 3–5 are the expected shape of the project, not settled decisions; adjust as the
work shows what is needed.
