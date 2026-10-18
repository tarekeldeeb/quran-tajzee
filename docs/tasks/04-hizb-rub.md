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
- **Objective:** for each container, solved exactly by the Task 3 dynamic program:

```
cuts only at phrase starts
1. minimise   max_q |S_q − T| / T          (the worst unit)
2. then       Σ_q (S_q − T)²               (among cuts reaching that worst)
```

## Results

| | traditional | new |
|---|---|---|
| hizb, worst (of ½ juz) | ±13.9% | ±3.7% |
| rubʿ, worst (of ¼ hizb) | ±38% | ±24% |
| longest/shortest rubʿ, whole Quran | 2.19× | 1.65× |
| hizb and rubʿ starting inside a phrase | 79 of 210 | **0** |

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
