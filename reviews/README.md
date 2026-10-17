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

## Rounds

| round | scope | outcome |
|-------|-------|---------|
| `2026-10-17-pilot` | Al-Fatiha, Al-Baqarah 1–77 (of a pilot covering 1, 2:1–141, Juz ʿAmma) | Merges preferred: 1:1–7, 2:8–16, 2:17–20, 2:34–37, 2:49–57. Prompted larger phrases across the whole list. |
