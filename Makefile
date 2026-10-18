PY ?= python3

.PHONY: validate test review scores juz rub check clean

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

check: validate test review

clean:
	rm -rf build
