# Paper

`main.tex` is the IEEE conference paper (IEEEtran, at most 4 pages) on this work. Every result it
quotes comes from `numbers.tex`, which `scripts/paper_numbers.py` writes from the committed data,
so the paper stays in step with the analyses.

```sh
make paper        # numbers.tex, then main.pdf (XeLaTeX)
```

It needs XeLaTeX, IEEEtran, polyglossia/bidi, pgfplots and the Amiri font (Debian/Ubuntu:
`texlive-xetex texlive-publishers texlive-lang-arabic texlive-pictures fonts-hosny-amiri`).
