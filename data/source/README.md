# Source text

`quran-uthmani.txt` is the **Tanzil Quran Text (Uthmani, Version 1.1)**, copied verbatim,
licence header included, from [tanzil.net](https://tanzil.net).

- Format: one aya per line, `sura|aya|text`; lines starting with `#` are the licence header.
- 6,236 ayat in 114 surahs (Kufan count).
- In this file the basmala opens aya 1 of each surah except At-Tawba (9). In Al-Fatiha it
  *is* aya 1.

Per the Tanzil licence, the text must not be modified, its source must be credited with a
link to tanzil.net, and this notice must stay in derived files. Check
<https://tanzil.net/updates/> before replacing it with a newer version, and re-run
`make check` afterwards.

## Traditional divisions

`hafs-rub-start-ayahs.json` lists the global aya index (1–6236, Tanzil order) where each
of the 240 traditional rub' (quarter-hizb) of the Hafs Mushaf starts, with a leading `0`
and a closing `6237`. Every 4th rub' starts a hizb and every 8th a juz. Copied from
[quran-nazm](https://github.com/tarekeldeeb/quran-nazm), which takes it from
`HizbQuarterList` in the [quran-meta](https://www.npmjs.com/package/quran-meta) package
(MIT). Used only as the baseline the new divisions are compared against.
