# Task 1 — Subject phrases

**Status:** complete for the whole Quran and reviewed.

## Goal

Divide the complete Tanzil text into *subject phrases* (مقاطع موضوعية): runs of 1–10
consecutive ayat that share one subject, the fewer ayat the better, as long as the subject
stays whole. These phrases are the only places a new Juz may start, so they guarantee
every later division starts at a meaningful point.

## Method

1. Read each surah in compact form (`python scripts/dump_text.py <sura> --words 8`).
2. Cut at shifts of subject: a new story or story beat, a new address (يا أيها الذين آمنوا،
   يا أيها الناس، قل…), a new ruling, a turn from argument to warning or from punishment to
   reward.
3. Keep units that read as one passage together, up to 10 ayat: a whole short story, a
   list of attributes, a debate exchange, a parable with its conclusion.
4. Give each phrase a short Arabic topic.
5. `make validate` checks the result covers every aya once with 1–10 ayat per phrase.

The pilot (Al-Fatiha, Al-Baqarah 1–141, Juz ʿAmma) started from small phrases (3.9 ayat
on average). Review merged single ayat into their neighbours and kept story units of up to
9 ayat together, so the full list was drafted at that larger size (5.7 on average).

## Review loop

1. `make review` builds `build/review.html`, a self-contained page with every phrase and
   its text, one surah at a time.
2. On the published page, each phrase can be approved, merged with the next, split after
   an aya, or given a corrected topic, with an optional note. Marks are saved as you go.
3. Export the marks into `reviews/<date>-<name>/marks.json` and apply them with
   `scripts/apply_reviews.py` (see `reviews/README.md`).
4. Commit the updated `phrases.tsv`, then rebuild and republish the page.

## Open points

- Phrases produced by merges get joined topics; they need a short rewrite.
- The size range (1–10) is a hard limit. The preferred size (about 4–8) is set by review.
