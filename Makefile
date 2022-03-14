.DEFAULT_GOAL := all

.PHONY: install
install:
	poetry install
	@echo 'installed poetry environment'

.PHONY: format
format:
	isort --project=kvom kvom tests
	black --check kvom tests

.PHONY: format-diff
format-diff:
	isort --check --diff --project=kvom kvom tests
	black --check --diff kvom tests

.PHONY: mypy
mypy:
	mypy kvom

.PHONY: lint
lint: format-diff
	flake8 kvom tests

.PHONY: test
test:
	pytest --cov=kvom tests/

.PHONY: testcov
testcov: test
	@echo "building coverage html"
	@coverage html

.PHONY: all
all: lint mypy testcov

.PHONY: clean
clean:
	git clean -f -X -d

.PHONY: docs
docs:
	flake8 --max-line-length=80 docs/examples/
	python docs/build/main.py
	mkdocs build

.PHONY: docs-serve
docs-serve:
	python docs/build/main.py
	mkdocs serve
