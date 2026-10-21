# Subject phrases

`phrases.tsv` divides the whole Quran into **subject phrases**: short runs of consecutive
ayat that share one subject. They are the building blocks for the balanced Juz in later tasks.
A Juz boundary will only ever fall *between* phrases.

| column  | meaning                                   |
|---------|-------------------------------------------|
| `sura`  | surah number, 1–114                        |
| `from`  | first aya of the phrase                    |
| `to`    | last aya of the phrase (inclusive)         |
| `topic` | short Arabic description of the subject   |

The phrase id used everywhere else (review page, review marks) is `sura:from-to`.

## Rules

1. Every aya belongs to exactly one phrase; a phrase never crosses a surah boundary.
2. A phrase has **1 to 10 ayat**.
3. A phrase is one subject: a story beat, one ruling, one argument, one scene.
4. Prefer whole story units and argument units of roughly 4–8 ayat over very short pieces.
   A single-aya phrase is kept only when the aya stands alone (e.g. 2:177, 4:43, 73:20).

`make validate` enforces rules 1–2. Rules 3–4 are what review is for.

## Current state

- 1,172 phrases, 5.3 ayat on average (sizes: 1:37, 2:65, 3:111, 4:203, 5:241, 6:195, 7:133, 8:98, 9:56, 10:33).
- Round 2026-10-18 (`reviews/2026-10-18-hizb-splits/`) split 18 phrases: 7 where a new hizb
  starts, and 11 where a traditional juz starts.
- Round 2026-10-21 (`reviews/2026-10-21-rub-splits/`, approved) split 60 phrases where a new
  rubʿ starts.
- Al-Fatiha and Al-Baqarah 1–77 were reviewed in an early pilot (its files have been removed;
  the merges it asked for are in this list). The rest of the pilot (2:78–141, Juz ʿAmma) was then
  reworked to the larger phrase size that review asked for, and everything else is a first
  draft at that size. All of it is awaiting review.
