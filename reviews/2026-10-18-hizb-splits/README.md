# Review round 2026-10-18: hizb splits

The second hizb of every traditional juz was checked one by one. For each juz:

1. Find the aya end that halves the juz best (the 50/50 size mix).
2. If that point opens a phrase, keep it.
3. If it falls inside a phrase, read the text at it and at the other candidates closer to the
   middle than the current hizb start.
4. Split the phrase only at a complete stop (*waqf tāmm*) that opens a new ruling, scene or
   subject, where the next aya does not lean on the one before it. Otherwise keep the current
   start, even if it is less even.

The 11 phrases that a traditional juz start falls inside were split as well, because those
juz starts are also hizb starts and every boundary must open a phrase. Splits with both new
topics: `splits.tsv`. Applied with `python scripts/apply_splits.py reviews/2026-10-18-hizb-splits/splits.tsv --write`.

## Decisions, juz by juz

The percentage is the first hizb against ½ of its juz.

| juz | before | after | decision |
|---|---|---|---|
| 1 | 2:78 (+0.6%) | 2:78 (+0.6%) | keep: 2:77 «أولا يعلمون» answers 2:76 |
| 2 | 2:204 (+2.5%) | **2:203 (+0.7%)** | split: 2:203 a new ruling (the counted days); 2:202 «أولئك لهم نصيب» leans on 2:201 |
| 3 | 3:18 (−0.6%) | same | already the best point |
| 4 | 3:165 (−0.5%) | same | already the best point |
| 5 | 4:88 (+1.7%) | **4:86 (−0.5%)** | split: 4:86 the ruling on greetings, after «مقيتا» |
| 6 | 5:27 (+3.6%) | 5:27 (+3.6%) | keep: every closer point is inside the dialogue of Moses and his people |
| 7 | 6:33 (−1.6%) | 6:33 (−1.6%) | keep: 6:34 continues the consolation that 6:33 opens |
| 8 | 7:19 (+2.1%) | 7:19 (+2.1%) | keep: every closer point is inside the dialogue with Iblīs |
| 9 | 7:163 (−2.0%) | 7:163 (−2.0%) | keep: 7:164 is inside the story of the Sabbath |
| 10 | 9:29 (−3.7%) | **9:30 (−1.5%)** | split: 9:30 «وقالت اليهود» after «وهم صاغرون»; 9:31 leans on 9:30 |
| 11 | 10:26 (−3.0%) | **10:28 (+0.4%)** | split: 10:28 «ويوم نحشرهم» a new scene, after «هم فيها خالدون» |
| 12 | 11:91 (+3.5%) | 11:91 (+3.5%) | keep: 11:88 would separate Shuʿayb's answer from his people's question |
| 13 | 13:19 (+1.5%) | 13:19 (+1.5%) | keep: 13:18 applies the parable of 13:17 |
| 14 | 16:41 (−1.2%) | **16:43 (+0.7%)** | split: 16:43 «وما أرسلنا من قبلك» a new subject; 16:42 describes 16:41 |
| 15 | 17:97 (+0.0%) | same | already the best point |
| 16 | 19:96 (−0.0%) | same | already the best point |
| 17 | 22:1 (−0.4%) | same | already the best point (a surah opening) |
| 18 | 24:21 (+1.7%) | **24:19 (−0.3%)** | split: 24:19 the threat to those who love indecency spread, after «والله عليم حكيم» |
| 19 | 26:116 (+0.2%) | 26:116 (+0.2%) | keep: 26:115 is inside Nūḥ's speech |
| 20 | 28:52 (+1.9%) | 28:52 (+1.9%) | keep: 28:50 is the second half of a condition; 28:51 leans forward into 28:52 |
| 21 | 31:12 (−0.1%) | same | already the best point |
| 22 | 34:34 (+2.9%) | 34:34 (+2.9%) | keep: 34:33 is inside the dispute of the weak and the arrogant |
| 23 | 37:158 (+0.2%) | same | already the best point |
| 24 | 40:41 (−1.3%) | 40:41 (−1.3%) | keep: 40:42–43 continue the believer's speech |
| 25 | 43:40 (+1.4%) | 43:40 (+1.4%) | keep: 43:38–39 continue the scene of the companion devil |
| 26 | 48:11 (+0.6%) | same | already the best point |
| 27 | 55:26 (+1.4%) | **55:24 (+0.5%)** | split: 55:24 the ships, a new blessing after the refrain |
| 28 | 61:5 (−0.4%) | same | already the best point |
| 29 | 72:1 (+1.4%) | 72:1 (+1.4%) | keep: the opening of Sūrat al-Jinn, rather than −1.1% at Nūḥ's duʿāʾ (71:26) |
| 30 | 87:9 (+0.0%) | same | already the best point |

Result: 7 hizb splits plus 11 juz splits, giving 1,112 phrases (from 1,094). The worst hizb is
±3.6% (traditional ±13.9%) and the hizb CV 1.4% (traditional 6.9%). No hizb or juz boundary
falls inside a phrase.
