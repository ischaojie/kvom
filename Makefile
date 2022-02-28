.DEFAULT_GOAL := all

.PHONY: install
install:
	poetry install
	@echo 'installed poetry environment'

.PHONY: format
format:
	isort --check --diff --project=kvom kvom tests
	black --check --diff kvom tests

.PHONY: lint
lint: format
	flake8 kvom tests

.PHONY: mypy
mypy:
	mypy kvom

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
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]'`
	rm -f `find . -type f -name '*~'`
	rm -f `find . -type f -name '.*~'`
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf dist
	python setup.py clean
	rm -rf site
	rm -rf docs/_build
	rm -rf docs/.changelog.md docs/.version.md docs/.tmp_schema_mappings.html
	rm -rf kvom/test.db
	rm -rf coverage.xml

.PHONY: docs
docs:
	flake8 --max-line-length=80 docs/examples/
	python docs/build/main.py
	mkdocs build

.PHONY: docs-serve
docs-serve:
	python docs/build/main.py
	mkdocs serve
