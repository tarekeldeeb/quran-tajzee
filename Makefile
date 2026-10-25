PY ?= python3

.PHONY: validate test review scores juz rub waqf paper check clean

validate:            ## check phrases.tsv covers every aya once, 1..10 ayat each
	$(PY) scripts/validate_phrases.py

test:                ## run unit tests
	$(PY) -m unittest discover -s tests -t . -v

review:              ## build build/review.html from phrases.tsv
	$(PY) scripts/build_review.py

scores:              ## phrase scores and analysis from the committed per-aya scores
	$(PY) scripts/score_phrases.py
	$(PY) scripts/analyze_scores.py

juz:                 ## solve the 30 balanced juz and write the analysis
	$(PY) scripts/solve_juz.py
	$(PY) scripts/analyze_juz.py

rub:                 ## hizb and rub' inside the traditional juz, and the analysis
	$(PY) scripts/solve_rub.py
	$(PY) scripts/analyze_rub.py
	$(PY) scripts/final_analysis.py
	$(PY) scripts/analyze_traditional.py
	$(PY) scripts/analyze_stops.py

waqf:                ## data/source/waqf/ from the OpenITI texts (downloads them into build/)
	$(PY) scripts/extract_waqf.py

paper:               ## paper/numbers.tex from the data, then paper/main.pdf (XeLaTeX)
	$(PY) scripts/paper_numbers.py
	cd paper && latexmk -xelatex -interaction=nonstopmode main.tex

check: validate test review

clean:
	rm -rf build
