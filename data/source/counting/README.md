# Counting schools (عدّ الآي)

`book-boundary-primitives.json` lists every disputed aya boundary of the Quran, anchored by surah,
Kūfī aya and the word the boundary follows, with the counting systems that count it as an aya end
(`kufi`, `madani-first`, `madani-last`, `makki`, `basri`, `dimashqi`). Undisputed Kūfī ends are
implicit. The classical source is al-Dānī, *al-Bayān fī ʿadd āy al-Qurʾān*.

- Upstream: [quranpedia/qiraat-ayah-map](https://github.com/quranpedia/qiraat-ayah-map),
  `data/book-boundary-primitives.json`, commit `076255281ec6f76241d7e901e27072733d02a18d`,
  as vendored verbatim by [quran-ws/quran-text](https://github.com/quran-ws/quran-text)
  (`sources/counting/`).
- SHA-256: `63f7bed237871b174a342d5a88688302c06929105af8dc3c3810b4e795a7e6f1`
- Licence: MIT, Copyright (c) 2026 Quranpedia (below). Copied verbatim.

Used by `tajzee.rub.disputed_end`: every new hizb and rubʿ boundary must be an aya end agreed by
all six systems (فاصلة بلا خلاف), as al-Ṣafāqusī requires.

## MIT licence

Copyright (c) 2026 Quranpedia

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES
OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
