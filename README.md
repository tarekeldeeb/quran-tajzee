# Quran-Tajzee · قرآن تجزيء

New Juz definitions for the Quran that are **balanced** for reciters and typesetters and
**begin at meaningful boundaries**. Starting from the [Tanzil](https://tanzil.net) text,
the Quran is first divided into short subject phrases. Juz boundaries are then chosen only
between phrases, so that each part has a similar length and opens at the start of a subject.

## Status

**Task 1 — subject phrases** is drafted for the whole Quran: 6,236 ayat in 1,094 phrases of
1–10 ayat, now under review. See the [roadmap](docs/roadmap.md) for what comes next.

## Layout

```
data/
  source/quran-uthmani.txt    Tanzil Uthmani text 1.1 (verbatim, licence header kept)
  phrases/phrases.tsv         Task 1 output, the source of truth: sura, from, to, topic
tajzee/                       shared Python library (no dependencies)
  quran.py                    load the text, surah names, diacritic-free view
  phrases.py                  load / save / validate the phrase list
  reviews.py                  apply review marks (approve, merge, split, topic)
scripts/                      command-line entry points, one per job
  validate_phrases.py         coverage and size checks
  dump_text.py                compact reading view of a passage
  build_review.py             build/review.html from the phrase list
  apply_reviews.py            apply an exported review round to phrases.tsv
review/template.html          the review page (marks stored by the hosting artifact)
reviews/                      one folder per review round: marks and the list reviewed
docs/                         roadmap and one document per task
tests/                        unit tests (python -m unittest)
```

## Use

Python 3.10+ and nothing else.

```sh
make validate   # every aya covered once, 1..10 ayat per phrase
make test       # unit tests
make review     # build build/review.html
python scripts/dump_text.py 18 --words 8      # read Al-Kahf compactly
```

CI runs `validate`, the tests and the review build on every push.

## License

Quran-Tajzee is released under the **Waqf General Public License 2.0** (رخصة وقف العامّة).
The project is a perpetual endowment (وقف) for the benefit of all. The authoritative
license text is the Arabic `LICENSE`; `LICENSE-en` is the informal English translation.
See the [official Waqf license repository](https://github.com/ojuba-org/waqf).

The Quran text in `data/source/` is the Tanzil Quran Text (Uthmani, Version 1.1),
© Tanzil Project, and stays under its own terms: used verbatim, with its licence notice,
credited with a link to [tanzil.net](https://tanzil.net). See `data/source/README.md`.
