# Task 4 — Hizb and rubʿ inside the traditional juz

**Status:** solved for the current phrase list. Output: `data/rub/hizb.tsv`,
`data/rub/rub.tsv`. Numbers: [04-hizb-rub-analysis.md](04-hizb-rub-analysis.md). The whole
division: [final analysis](../final-analysis.md). Background:
[the Ghayth al-Nafʿ study](../research/ghayth-al-naf.md).

## Decision: keep the traditional juz

Task 3 showed that the traditional juz are already fairly even: ±6.2% on the mix, against
±5.0% optimised. The imbalance is in the finer divisions. Relative to their share, the
traditional hizb reach ±14% of half a juz and the rubʿ ±38% of a quarter-hizb. So the 30 juz
stay as in the Madina Mushaf, and the hizb and rubʿ inside them are re-cut.

## Model

- **Unit:** the aya. Its size is the Task 2/3 mix: ½ recitation share and ½ print share, with the basmala at surah
  openings and the space after each aya.
- **Nested, as the divisions are:**
  - Each juz is cut into 2 hizb, each with a target of ½ of the juz.
  - Each hizb is then cut into 4 rubʿ, each with a target of ¼ of the hizb.
- **Meaning:** every new boundary is a phrase start, so a hizb or rubʿ always opens a subject (Task 1).
  This is the analogue of al-Ṣafāqusī's *waqf tāmm*. The juz starts are fixed. In 11 of them the
  traditional start falls inside a phrase, and those phrases are proposed for splitting.
- **First ten ayat:** no hizb or rubʿ starts at aya 2–10 of a surah. It starts at the surah itself or
  10 or more ayat in. The traditional juz are exempt (juz 12 starts at 11:6).
- **Objective:** for each container, solved exactly by the Task 3 dynamic program:

```
cuts only at phrase starts
1. minimise   max_q |S_q − T| / T          (the worst unit)
2. then       Σ_q (S_q − T)²               (among cuts reaching that worst)
```

## Results

| | traditional | new |
|---|---|---|
| hizb, worst (of ½ juz) | ±13.9% | ±3.6% |
| hizb, CV | 6.9% | 1.6% |
| rubʿ, worst (of ¼ hizb) | ±38% | ±30.7% |
| rubʿ, CV | 11.7% | 7.6% |
| longest/shortest rubʿ, whole Quran | 2.19× | 1.81× |
| hizb and rubʿ starting at aya 2–10 of a surah | 12 | **0** |
| hizb and rubʿ starting inside a phrase | 79 of 210 | **0** |

## Review round 1: hizb (2026-10-18, approved 2026-10-21)

Every hizb was checked on its own. Where the point that best halves the juz fell inside a
phrase, the text was read and the phrase was split only at a complete stop that opens a new
subject. That gave 7 splits. The 11 phrases cut by traditional juz starts were split too. The
decisions, juz by juz, are in [reviews/2026-10-18-hizb-splits](../../reviews/2026-10-18-hizb-splits/README.md).
Where meaning ruled out a closer point, the hizb is kept less even: juz 6 +3.6%, juz 12 +3.5%,
juz 22 +2.9%, and juz 29 keeps the opening of Sūrat al-Jinn.

## Review round 2: rubʿ (2026-10-21, proposed)

With the approved hizb fixed (`data/rub/hizb-approved.tsv`), every quarter boundary more than 3% of a
quarter from its even position was checked the same way. That was 132 boundaries and 422 candidates
read. 61 phrases were split at complete stops, and 71 boundaries were kept because every closer point is
a turn of a story or dialogue. Quarter CV went from 9.2% to 5.9% and the worst quarter from ±23.8% to
±19.4%. The first-ten-ayat rule, added the same day, then rejected 6 of those splits, moved the second
hizb of juz 28 and 30 to their surah openings (61:1, 87:1), and a supplementary reading added 4 splits:
quarter CV 7.6%, worst ±30.7%. Decisions: [reviews/2026-10-21-rub-splits](../../reviews/2026-10-21-rub-splits/README.md).

## Balance through review

Phrase granularity limits rubʿ balance: there are about 4.6 phrases per rubʿ. The `penalized`
objective (`--objective penalized`) shows how far the rubʿ could go if they were allowed to start
inside phrases: ±9.4% with 60 such starts. `data/rub/phrase-splits.tsv` lists those 60 places as
phrase splits for review, with reason `balance`. It also lists the 11 juz starts, with reason `juz`.

- An accepted split adds a phrase start, so the default improves without ever cutting a phrase.
- A rejected split leaves the phrase as it is.

## Run

```sh
python scripts/solve_rub.py            # data/rub/hizb.tsv, rub.tsv, solution.json, phrase-splits.tsv
python scripts/analyze_rub.py          # docs/tasks/04-hizb-rub-analysis.md, data/rub/analysis.json,
                                       # data/rub/traditional-phrase-cuts.tsv
python scripts/final_analysis.py       # docs/final-analysis.md
python scripts/solve_rub.py --objective penalized --out /tmp/rub.tsv   # mid-phrase rubʿ allowed
```

`make rub` runs all three.

## Decisions to revisit

- **Surah openings.** The new hizb open fewer surahs than the traditional ones (2 against 7 of 30).
  A surah preference like the one in Task 3 could be added.
- **Al-Ṣafāqusī's alternatives** (Maghāriba and Mashāriqa boundaries) could be preferred cut points.
- **Agreement across the counting schools** (فاصلة بلا خلاف) is not checked yet.
