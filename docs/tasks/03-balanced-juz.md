# Task 3 — Balanced juz

**Status:** solved for the current phrase list. Result: `data/juz/juz.tsv`; numbers and
comparison: [03-juz-analysis.md](03-juz-analysis.md).

## Goal

Distribute the 1,094 subject phrases into 30 consecutive juz that are as even as possible,
weighing recitation and typesetting 50/50. A juz may start only where a phrase starts, so
every juz opens on a subject.

## Model

For phrase i, `r_i` is its recitation score and `p_i` its typesetting score (Task 2). Surah
openings are added to the phrase that opens the surah:

- recitation: the basmala, 19 harakat (all surahs but Al-Fatiha, whose basmala is aya 1, and
  At-Tawba);
- typesetting: the text width only, as Task 2 defines it. Printed header lines can be
  included with `--header-weight` (see the analysis, section 5).

The two scores have different units, so each is taken as a share of its total and the two
shares are mixed:

```
c_i = w · r_i / R + (1 − w) · p_i / P        w = 0.5,  Σ c_i = 1,  target T = 1/30
```

A division is 29 cut points in the phrase sequence. Juz j has size `S_j`, the sum of its
`c_i`.

## Surah-break penalty (default)

Starting a juz in the middle of a surah is penalised. With B the number of juz that start
mid-surah:

```
minimise   Σ_j ((S_j − T) / T)²  +  p² · B        subject to  |S_j − T| / T ≤ cap
```

p reads as "breaking a surah costs as much as one juz being off its target by p". Defaults
are p = 4% and cap = ±5%. The analysis sweeps p and shows 4% at the knee: 10 juz open a surah
(20 start mid-surah, against 21 for the traditional juz) and every juz is within ±3.8%.
Without the penalty, only 2 juz open a surah but the worst juz is ±2.1%. A juz that opens a
surah costs nothing; the first juz always starts at 1:1. The penalty is a per-cut cost, so
the dynamic program below stays exact.

## Solver

Without the penalty (`--objective minimax+lsq`), lexicographic, exact:

1. **Minimax**: the smallest possible worst deviation `D* = min max_j |S_j − T|`.
2. **Least squares**: among divisions with every `|S_j − T| ≤ D*`, the smallest `Σ_j (S_j − T)²`.

Each step is a dynamic program over (juz used, phrases consumed):

```
F_k(i) = min over j < i of  [ F_{k−1}(j)  ⊕  g(C_i − C_j) ]
```

with C the prefix sums of c. For step 1, ⊕ = max and g = |x − T|. For step 2, ⊕ = + and
g = (x − T)², with parts beyond D* excluded. The penalized objective is the second recursion
with g = ((x − T)/T)², plus p² whenever the part starting at phrase j opens mid-surah, and with
parts beyond the cap excluded. A juz is a contiguous run of phrases, so the
problem has optimal substructure and the DP returns the global optimum. It is not a
heuristic. Runtime is O(30 · n · W): about 5 s in pure Python for n = 1,094 phrases and a
window of W = 300 phrases per juz. The tests check the result against exhaustive search on
random small cases.

Other objectives (`--objective`):

| objective | meaning |
|---|---|
| `penalized` | default: least squares plus the surah-break penalty (`--break-penalty`, `--cap`) |
| `minimax+lsq` | as above, no penalty |
| `lsq` | least squares only |
| `minimax` | worst juz only |
| `each` | no mixing: the smallest worst deviation of *either* score, then least squares |

## Run

```sh
python scripts/solve_juz.py                      # data/juz/juz.tsv, data/juz/solution.json
python scripts/analyze_juz.py                    # docs/tasks/03-juz-analysis.md, data/juz/analysis.json
python scripts/solve_juz.py --break-penalty 0.05 --cap 0.06 --out /tmp/juz.tsv
python scripts/solve_juz.py --weight 0.7 --objective each --header-weight 1 --out /tmp/juz.tsv
```

`make juz` runs both, using only committed data.

## Output

`data/juz/juz.tsv`, one row per juz: start and end (sura:aya), phrases, ayat, words, both
scores, their deviation from the mean, the deviation of the mix, and the topic of the first
phrase.

## Decisions to revisit

- **Surah header lines** in print (analysis, section 6). Counted in full, Juz ʿAmma's 37 headers
  make the last juz long in print and short in recitation, at ±12.5% whatever its start. The
  default leaves them out, as in Task 2. A print layout can give juz 30 extra pages instead, as
  Quran-Nazm does.
- **Surah-break penalty**: p = 4% and cap ±5% are a proposal from the sweep in the analysis
  (section 4). Raising p opens more juz on surahs at a cost in balance.
- **Phrase review**: the balance limit is phrase granularity near the worst juz. Each review round
  changes the phrases, and re-running the solver gives the new exact optimum.
