# Quran-Tajzee · قرآن تجزيء

New Juz definitions for the Quran that are **balanced** for reciters and typesetters and
**begin at meaningful boundaries**. Starting from the [Tanzil](https://tanzil.net) text,
the Quran is first divided into short subject phrases. Juz boundaries are then chosen only
between phrases, so that each part has a similar length and opens at the start of a subject.

## Why: how the traditional quarters were drawn

The Madina Mushaf takes its juz, hizb and rubʿ from al-Ṣafāqusī's *Ghayth al-Nafʿ*
(d. 1118 AH). He states his method in the terminology section of the introduction (printed p. 25):

- **He does not compute the boundaries.** He follows only the agreed or the well-known positions:
  «وقد وقع للناس في تعيين أوائل الأحزاب خلاف ولا أمشي إلا على المتفق عليه أو المشهور».
- **Each quarter is a unit:** «وأذكر حكم كل ربع بانفراده».
- **Each quarter ends at a proper stop.** He names its last word, the kind of stop it allows and whether it
  ends an aya: «وأشير إلى انتهائه بذكر آخر كلمة منه مع ذكر حكم الوقف عليها وبيان هل هي من الفواصل أم لا».
  For example, at Al-Baqara 2:25 (printed p. 60) he writes «خالِدُونَ تام في أعلى درجاته وفاصلة ومنتهى الربع بإجماع»:
  a complete stop of the highest degree, an aya end, and the end of the quarter by consensus.

The measurements agree with this ([analysis](docs/research/traditional-divisions-analysis.md)):

- **The juz are close to equal.** Each starts on average 2.4% of a juz from an equal-letter position.
- **The quarters are not equal.** Inside their juz they lie 15% of a rubʿ from equal positions. That is 10× further than
  aya ends alone would force. Their lengths vary by 2.2×. They were drawn at the ends of thoughts, not by count.

**The issue.** The rule is sound, but the transmitted quarters keep it only partly. 90 of the
239 traditional boundaries fall inside a subject phrase, typically halfway through it, and some
open mid-story or mid-dialogue:

- juz 16 opens at «قال ألم أقل لك», in the dialogue of Mūsā and al-Khaḍir;
- juz 27 opens at «قال فما خطبكم أيها المرسلون», in the story of Ibrāhīm's guests;
- a hizb opens at «فنبذناه بالعراء», in the story of Yūnus.

So the quarters pay the price of uneven length without fully getting the meaningful boundaries
they were drawn for.

**This project fixes that.** It applies al-Ṣafāqusī's rule (a unit ends at the end of a thought)
to every boundary, and then chooses among the stops that satisfy it by measured length:
recitation and print width.

## Status

- **Task 1 — subject phrases**: drafted for the whole Quran, 6,236 ayat in 1,171 phrases of
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
  from [Ghayth al-Nafʿ](docs/research/ghayth-al-naf.md)), the hizb and then their quarters are
  re-cut exactly, only at phrase starts. Hizb go from ±14% to ±3.6% of half a juz (CV 6.9% → 1.4%), after a
  hizb-by-hizb review that split 7 phrases at complete stops, and the
  longest rubʿ from 2.19× the shortest to 1.81× (CV 11.7% → 7.6%) after a quarter review that
  split 59 phrases at complete stops; no hizb or rubʿ starts at aya 2–10 of a surah. The traditional hizb and rubʿ start inside a
  subject phrase 79 times out of 210; the new ones never do. See the
  [final analysis](docs/final-analysis.md).

See the [roadmap](docs/roadmap.md) for what comes next.

## Layout

```
data/
  source/quran-uthmani.txt    Tanzil Uthmani text 1.1 (verbatim, licence header kept)
  source/hafs-rub-start-ayahs.json   traditional rub' starts (baseline for comparison)
  phrases/phrases.tsv         Task 1 output, the source of truth: sura, from, to, topic
  scores/                     Task 2 output: per-aya and per-phrase recitation and typesetting scores
  juz/juz.tsv                 Task 3 output: the 30 balanced juz (alternative)
  rub/hizb.tsv, rub/rub.tsv   Task 4 output: 60 hizb and 240 rubʿ inside the traditional juz
  rub/traditional-phrase-cuts.tsv   traditional boundaries that start inside a phrase
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
  final_analysis.py           final analysis of the complete division
  analyze_traditional.py      the traditional rubʿ measured: letter counts, stops, phrases
  apply_splits.py             apply a round of phrase splits with new topics
  paper_numbers.py            paper/numbers.tex: every number the paper quotes
review/template.html          the review page (marks stored by the hosting artifact)
reviews/                      one folder per review round: marks and the list reviewed
docs/                         roadmap, one document per task, research notes
paper/                        IEEE paper (4 pages max); numbers generated from the data
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
make rub        # hizb and rubʿ inside the traditional juz + analysis + final analysis
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
