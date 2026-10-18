# Roadmap

Quran-Tajzee derives new Juz definitions that are **balanced** in length for reciters and
typesetters while **starting only at meaningful points** in the text.

Each task gets a document in `docs/tasks/NN-name.md`, its data under `data/<name>/`, its
code in `tajzee/` (library) and `scripts/` (command-line entry points), and tests in `tests/`.

| # | Task | Output | Status |
|---|------|--------|--------|
| 1 | [Subject phrases](tasks/01-phrase-segmentation.md): split the text into 1–10 aya phrases by subject | `data/phrases/phrases.tsv` | draft done, in review |
| 2 | [Length scores](tasks/02-length-scores.md): recitation (Hafs madd-weighted phonemes) and typesetting (DigitalKhatt width) per aya and phrase, with [analysis](tasks/02-scores-analysis.md) | `data/scores/` | done |
| 3 | [Balanced juz](tasks/03-balanced-juz.md): exact solver dividing the phrases into 30 juz on a 50/50 mix of both scores, with [analysis](tasks/03-juz-analysis.md) | `data/juz/juz.tsv` | done; kept as an alternative, the project now uses the traditional juz (Task 4) |
| 4 | [Hizb and rubʿ](tasks/04-hizb-rub.md) inside the **traditional** juz (Madina Mushaf, after [Ghayth al-Nafʿ](research/ghayth-al-naf.md)), with [analysis](tasks/04-hizb-rub-analysis.md) and the [final analysis](final-analysis.md) | `data/rub/` | done (re-solve after each phrase review) |
| 5 | Phrase review round 2: the 71 proposed splits in `data/rub/phrase-splits.tsv` (11 juz, 60 balance) | `data/phrases/phrases.tsv` | next |
| 6 | Tabulate Ghayth al-Nafʿ's 240 boundaries and their Maghāriba/Mashāriqa alternatives as preferred cut points | `data/source/` | planned |

Tasks 3–5 are the expected shape of the project, not settled decisions; adjust as the
work shows what is needed.
