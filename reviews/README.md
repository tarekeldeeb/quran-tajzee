# Review rounds

Each review round gets a folder named `YYYY-MM-DD-<name>/` holding:

- `phrases-*.tsv` – the phrase list exactly as it was when reviewed (only when it differs
  from a commit of `data/phrases/phrases.tsv`, e.g. the pilot, which covered part of the Quran)
- `marks.json` – the marks exported from the review page

A mark is `{"seg": "sura:from-to", "status": "ok" | "merge" | "split" | "topic",
"splitAfter": <aya>, "topic": "...", "note": "...", "at": "<ISO time>"}`.

Apply a round with:

```sh
python scripts/apply_reviews.py reviews/<round>/marks.json            # dry run
python scripts/apply_reviews.py reviews/<round>/marks.json --write    # update phrases.tsv
```

Merged phrases get their topics joined with `، `. Tidy those by hand or in the next round.
Marks on phrases whose boundaries have since changed are reported as stale and skipped.

## Split rounds (division-driven)

A round that splits phrases to serve the divisions keeps a `splits.tsv` instead of marks: one
row per candidate split, accepted or rejected, with its reason and the topics of both halves.
Columns: `juz sura from to split_after new_start hizb_dev_pct reason decision topic_first
topic_second note`.

`data/phrases/phrases.tsv` is rebuilt from the reading of the text (every listed split merged
back) plus every accepted row, so a decision can be flipped either way:

```sh
python scripts/apply_splits.py            # dry run: what changes
python scripts/apply_splits.py --write    # rebuild phrases.tsv
make scores juz rub paper                 # re-solve and refresh the reports
python scripts/review_hizb.py             # refresh the round's README
```

## Rounds

| round | scope | outcome |
|-------|-------|---------|
| `2026-10-18-hizb-splits` | The second hizb of every juz, and the 11 traditional juz starts inside a phrase | 57 candidates read: 7 hizb splits accepted, 50 rejected with reasons; 11 juz splits. Worst hizb ±3.6%. See its README. |
| `2026-10-17-pilot` | Al-Fatiha, Al-Baqarah 1–77 (of a pilot covering 1, 2:1–141, Juz ʿAmma) | Merges preferred: 1:1–7, 2:8–16, 2:17–20, 2:34–37, 2:49–57. Prompted larger phrases across the whole list. |
