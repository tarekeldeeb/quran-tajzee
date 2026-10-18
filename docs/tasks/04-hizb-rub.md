# Task 4 — Hizb and rubʿ inside the traditional juz

**Status:** solved for the current phrase list. Output: `data/rub/rub.tsv`. Numbers and
comparison: [04-hizb-rub-analysis.md](04-hizb-rub-analysis.md). Background:
[the Ghayth al-Nafʿ study](../research/ghayth-al-naf.md).

## Decision: keep the traditional juz

Task 3 showed that the traditional juz are already fairly even: ±6.2% on the mix, against
±5.0% for the optimised ones, with phrase granularity setting the limit. The imbalance is in
the finer divisions. Relative to their share of the juz, the traditional hizb reach ±14% and
the rubʿ ±35%. So the 30 juz stay as in the Madina Mushaf, and only the 2 hizb and 8 rubʿ
inside each juz are re-cut. Task 3's solver and its divisions remain available as an
alternative.

## Model

- **Unit:** the aya. Every boundary is an aya end, as in the tradition.
- **Size:** the Task 2/3 mix, `c = ½ · recitation share + ½ · print share`. Recitation counts the basmala
  at surah openings. Print counts the text and the space after each aya.
- **Target:** each rubʿ is 1/8 of *its own* juz. A hizb is then 1/2 of the juz.
- **Meaning:**
  - A **hizb** must start at a phrase start, i.e. a new subject (Task 1). This is the analogue of al-Ṣafāqusī's *waqf tāmm*.
  - A **rubʿ** should start at a phrase start too. It may start at another aya end inside a phrase, at a
    penalty m: such a start costs as much as a rubʿ m off its target.
  - A juz start that falls inside a phrase splits that phrase. The juz are fixed.

For each juz, solved exactly by the Task 3 dynamic program:

```
minimise   Σ_q ((S_q − T_J) / T_J)²  +  m² · (rubʿ starts inside a phrase)
subject to |S_q − T_J| / T_J ≤ cap,     hizb start (rubʿ 5) at a phrase start

defaults:  m = 10%,  cap = ±10%
```

## Results (default)

| | traditional | new |
|---|---|---|
| rubʿ, worst (of 1/8 juz) | ±35% | ±10% |
| rubʿ, CV | 13.4% | 4.3% |
| hizb, worst (of 1/2 juz) | ±14% | ±3.7% |
| rubʿ starting inside a phrase | 79 of 210 | 58 of 210 |

The two scores move together, so balancing the mix balances each.

## Review loop

`data/rub/phrase-splits.tsv` lists every phrase that a boundary falls inside, as a proposed
split with `split_after` as in the review marks. There are two kinds:

- `juz`: one of the 11 traditional juz starts falls inside the phrase.
- `rub`: the solver started a rubʿ inside the phrase.

After a review:

- An accepted split becomes a phrase start, and the rubʿ then opens a subject.
- A rejected one keeps the phrase whole. Re-solving with a higher m, or adding that phrase as a constraint, moves the rubʿ.

Finer phrases are what let rubʿ balance better. With phrase starts only, the worst rubʿ is ±24%.

## Run

```sh
python scripts/solve_rub.py          # data/rub/rub.tsv, solution.json, phrase-splits.tsv
python scripts/analyze_rub.py        # docs/tasks/04-hizb-rub-analysis.md, data/rub/analysis.json
python scripts/solve_rub.py --mid-phrase inf --cap inf --out /tmp/rub.tsv   # phrase starts only
```

`make rub` runs both.

## Decisions to revisit

- **Mid-phrase penalty m and cap.** The default 10% / ±10% trades about 58 review items for
  ±10% rubʿ. See the sweep in the analysis, section 2.
- **Al-Ṣafāqusī's alternatives** (Maghāriba and Mashāriqa boundaries) could serve as preferred cut
  points once his 240 boundaries are tabulated.
- **Agreement across the counting schools** (فاصلة بلا خلاف) is not checked yet.
