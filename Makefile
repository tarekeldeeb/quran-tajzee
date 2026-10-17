PY ?= python3

.PHONY: validate test review scores check clean

validate:            ## check phrases.tsv covers every aya once, 1..10 ayat each
	$(PY) scripts/validate_phrases.py

test:                ## run unit tests
	$(PY) -m unittest discover -s tests -t . -v

review:              ## build build/review.html from phrases.tsv
	$(PY) scripts/build_review.py

scores:              ## phrase scores and analysis from the committed per-aya scores
	$(PY) scripts/score_phrases.py
	$(PY) scripts/analyze_scores.py

check: validate test review

clean:
	rm -rf build
