# Task 4 — Hizb and rubʿ inside the traditional juz

**Status:** solved and reviewed: both review rounds (hizb, rubʿ) approved on 2026-10-21. Output: `data/rub/hizb.tsv`,
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
- **Opening ayat:** no hizb or rubʿ starts at aya 2–7 of a surah. It starts at the surah itself or
  at aya 8 or later. Exempt: juz 28, whose surahs of 11–24 ayat leave too few admissible starts, and
  the traditional juz starts (juz 12 starts at 11:6).
- **Agreed aya ends:** every boundary is an aya end in all six counting systems (فاصلة بلا خلاف),
  checked against al-Dānī's *al-Bayān* (`data/source/counting/`). 134 Kūfī aya ends are disputed; the
  traditional divisions never start after one, and two first solutions (20:42, 74:42) did, so the
  solver excludes them.
- **Objective:** for each container, solved exactly by the Task 3 dynamic program, cuts only at
  phrase starts. The hizb (approved in review, kept fixed) on the 50/50 mix S:

```
1. minimise   max_q |S_q − T| / T          (the worst unit)
2. then       Σ_q (S_q − T)²               (among cuts reaching that worst)
```

  The quarters weigh recitation R, print P and the pause before each cut, ⅓ each:

```
minimise  ⅓ Σ_q ((R_q − T_R)/T_R)²  +  ⅓ Σ_q ((P_q − T_P)/T_P)²  +  ⅓ Σ_cuts (0.05 · points)²
points:   surah end 1, تام 2, كاف 3, weaker (حسن، جائز، or not graded) 5, ليس بوقف 9
```

  One point is worth 5% of a quarter (`rub.POINT_VALUE`). Every phrase start's category and points
  are in `data/rub/phrase-pauses.tsv`. Against the mix-only objective the pause term moves 16 quarters,
  lowers the pause points from 520 to 493 and the starts below كاف from 9 to 3, at a quarter CV of
  6.5% → 6.8%.

## Results

| | traditional | new |
|---|---|---|
| hizb, worst (of ½ juz) | ±13.9% | ±3.6% |
| hizb, CV | 6.9% | 1.4% |
| rubʿ, worst (of ¼ hizb) | ±38% | ±20.8% |
| rubʿ, CV | 11.7% | 6.8% |
| longest/shortest rubʿ, whole Quran | 2.19× | 1.57× |
| hizb and rubʿ at aya 2–7 of a surah (juz 28 and juz starts exempt) | 2 | **0** |
| hizb and rubʿ starting inside a phrase | 79 of 210 | **0** |

## Review round 1: hizb (2026-10-18, approved 2026-10-21)

Every hizb was checked on its own. Where the point that best halves the juz fell inside a
phrase, the text was read and the phrase was split only at a complete stop that opens a new
subject. That gave 7 splits. The 11 phrases cut by traditional juz starts were split too. The
decisions, juz by juz, are in [reviews/2026-10-18-hizb-splits](../../reviews/2026-10-18-hizb-splits/README.md).
Where meaning ruled out a closer point, the hizb is kept less even: juz 6 +3.6%, juz 12 +3.5%,
juz 22 +2.9%, and juz 29 keeps the opening of Sūrat al-Jinn.

## Review round 2: rubʿ (2026-10-21, approved 2026-10-21)

With the approved hizb fixed (`data/rub/hizb-approved.tsv`), every quarter boundary more than 3% of a
quarter from its even position was checked the same way. That was 132 boundaries and 422 candidates
read. 61 phrases were split at complete stops, and 71 boundaries were kept because every closer point is
a turn of a story or dialogue. Quarter CV went from 9.2% to 5.9% and the worst quarter from ±23.8% to
±19.4%. The opening-ayat rule (no start at aya 2–7 of a surah, juz 28 exempt), added the same day, then
rejected 5 of those splits, and a supplementary reading added 4: quarter CV 6.4%, worst ±20.8%; the counting rule then moved two quarters (20:42 → 20:49, 74:42 → 74:38): CV 6.5%; the pause points (2026-10-25) then moved 16 quarters: CV 6.8%. Decisions: [reviews/2026-10-21-rub-splits](../../reviews/2026-10-21-rub-splits/README.md).

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
