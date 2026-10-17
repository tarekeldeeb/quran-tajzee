PY ?= python3

.PHONY: validate test review check clean

validate:            ## check phrases.tsv covers every aya once, 1..10 ayat each
	$(PY) scripts/validate_phrases.py

test:                ## run unit tests
	$(PY) -m unittest discover -s tests -t . -v

review:              ## build build/review.html from phrases.tsv
	$(PY) scripts/build_review.py

check: validate test review

clean:
	rm -rf build
