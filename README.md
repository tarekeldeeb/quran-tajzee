# Quran-Tajzee · قرآن تجزيء

New Juz definitions for the Quran that are **balanced** for reciters and typesetters and
**begin at meaningful boundaries**. Starting from the [Tanzil](https://tanzil.net) text,
the Quran is first divided into short subject phrases. Juz boundaries are then chosen only
between phrases, so that each part has a similar length and opens at the start of a subject.

## Status

- **Task 1 — subject phrases**: drafted for the whole Quran, 6,236 ayat in 1,094 phrases of
  1–10 ayat, under review.
- **Task 2 — length scores**: every aya and phrase scored for recitation (Hafs madd-weighted
  phonemes, via tajweed-embeddings) and typesetting (DigitalKhatt width, via quran-nazm).
  See the [analysis](docs/tasks/02-scores-analysis.md).
- **Task 3 — balanced juz**: an exact solver divides the phrases into 30 juz on a 50/50 mix
  of both scores, with a penalty for starting a juz mid-surah that is highest for the last 5 juz.
  Every juz is within ±5% of the target (traditional: ±6.2%), and 4 of the last 5 open a surah.
  See the [analysis](docs/tasks/03-juz-analysis.md). The gain over the traditional juz is small,
  so the project keeps the traditional juz.
- **Task 4 — hizb and rubʿ**: inside the traditional juz (Madina Mushaf, whose divisions come
  from [Ghayth al-Nafʿ](docs/research/ghayth-al-naf.md)), the 2 hizb and 8 rubʿ are re-cut
  exactly. Hizb go from ±14% to ±3.7% of half a juz, rubʿ from ±35% to ±10% of an eighth,
  and every hizb opens a subject. See the [analysis](docs/tasks/04-hizb-rub-analysis.md).

See the [roadmap](docs/roadmap.md) for what comes next.

## Layout

```
data/
  source/quran-uthmani.txt    Tanzil Uthmani text 1.1 (verbatim, licence header kept)
  source/hafs-rub-start-ayahs.json   traditional rub' starts (baseline for comparison)
  phrases/phrases.tsv         Task 1 output, the source of truth: sura, from, to, topic
  scores/                     Task 2 output: per-aya and per-phrase recitation and typesetting scores
  juz/juz.tsv                 Task 3 output: the 30 balanced juz (alternative)
  rub/rub.tsv                 Task 4 output: 240 rubʿ / 60 hizb inside the traditional juz
  rub/phrase-splits.tsv       phrases a juz or rubʿ start falls inside (for review)
tajzee/                       shared Python library (no dependencies)
  quran.py                    load the text, surah names, diacritic-free view
  phrases.py                  load / save / validate the phrase list
  reviews.py                  apply review marks (approve, merge, split, topic)
  scores.py                   read the length scores; score any range of ayat
  juz.py                      exact partition solver (minimax + least squares DP)
  rub.py                      hizb and rubʿ inside the traditional juz
scripts/                      command-line entry points, one per job
  validate_phrases.py         coverage and size checks
  dump_text.py                compact reading view of a passage
  build_review.py             build/review.html from the phrase list
  apply_reviews.py            apply an exported review round to phrases.tsv
  score_recitation.py         per-aya recitation score (needs tajweed-embeddings)
  score_typesetting.py        per-aya DigitalKhatt width (needs quran-nazm, quran-madina-html)
  score_phrases.py            sum per-aya scores into phrases
  analyze_scores.py           numeric analysis report
  solve_juz.py                solve the 30 juz (weight, objective, header options)
  analyze_juz.py              juz analysis report
  solve_rub.py                solve the hizb and rubʿ (Task 4)
  analyze_rub.py              hizb and rubʿ analysis report
review/template.html          the review page (marks stored by the hosting artifact)
reviews/                      one folder per review round: marks and the list reviewed
docs/                         roadmap, one document per task, research notes
tests/                        unit tests (python -m unittest)
```

## Use

Python 3.10+ and nothing else.

```sh
make validate   # every aya covered once, 1..10 ayat per phrase
make test       # unit tests
make review     # build build/review.html
make scores     # phrase scores + analysis report from the committed per-aya scores
make juz        # solve the 30 juz + analysis report
make rub        # hizb and rubʿ inside the traditional juz + analysis report
python scripts/dump_text.py 18 --words 8      # read Al-Kahf compactly
```

CI runs `validate`, the tests, checks that the phrase scores, the juz division and the hizb/rubʿ division are
up to date, and the review build on every push. The per-aya scores need the external projects (see
[Task 2](docs/tasks/02-length-scores.md)); everything downstream needs only Python.

## License

Quran-Tajzee is released under the **Waqf General Public License 2.0** (رخصة وقف العامّة).
The project is a perpetual endowment (وقف) for the benefit of all. The authoritative
license text is the Arabic `LICENSE`; `LICENSE-en` is the informal English translation.
See the [official Waqf license repository](https://github.com/ojuba-org/waqf).

The Quran text in `data/source/` is the Tanzil Quran Text (Uthmani, Version 1.1),
© Tanzil Project, and stays under its own terms: used verbatim, with its licence notice,
credited with a link to [tanzil.net](https://tanzil.net). See `data/source/README.md`.
