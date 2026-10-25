# Pause grades from the classical works

Built by `scripts/extract_waqf.py` from the [OpenITI](https://github.com/OpenITI) texts (pinned commits
in the script). Only the grades and short quotes of the authors' notes are kept here, not the texts.

| book | OpenITI text |
|---|---|
| al-Dānī (d. 444), *al-Muktafā fī al-Waqf wa-l-Ibtidāʾ* | `0444AbuCamrDani.MuktafiFiWaqf.Shamela0026461-ara1` |
| al-Ushmūnī (d. c. 1100), *Manār al-Hudā fī Bayān al-Waqf wa-l-Ibtidāʾ* | `1100IbnCabdKarimAshmuniMisri.ManarHuda.Shamela0006496-ara1` |
| al-Ṣafāqusī (d. 1118), *Ghayth al-Nafʿ fī al-Qirāʾāt al-Sabʿ* | `1118IbnMuhammadNuriSafaqsi.GhaythNafc.Shamela0027083-ara1` |

## stops.tsv

One row per aya end that either book grades: `sura`, `aya`, and the grade word each book gives the end
of that aya (`muktafa`, `manar`; empty if it does not grade it). Grades: تام، أكفى، كاف، حسن، صالح،
جائز، ليس بوقف / لا وقف. Where a book gives several opinions («تام وقيل كاف»), the first is kept.

## ghayth-quarters.tsv

One row per quarter (1–240): `madina_end` (the aya before the Madina quarter start), `ghayth_end` (the
aya whose last word al-Ṣafāqusī names as the end of the quarter, empty where his note was not located),
`grade` (the first grade he gives it), `standing` (consensus, well-known, regional, some, stated: how
widely he says the end is accepted) and `note` (his words, from the grade to the end of the sentence,
with the alternatives he reports).

## Accuracy

Quotes are matched by consonant skeleton. Where both books grade an aya end they agree within one grade
96% of the time. Typical errors: a grade read from the next opinion in a long note, and the few
quarter notes Ghayth words unusually (7 not located). See `docs/research/stop-grades-analysis.md`.

The texts are classical works in the public domain; the digital editions are by al-Maktaba al-Shāmila
and OpenITI. Cite OpenITI (KITAB project) when reusing.
