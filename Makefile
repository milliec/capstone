# Four everyday commands. Run them from the repository root.
#   make install   set up .venv (Python 3.12) and install the app and test dependencies
#   make run       start the app on http://localhost:8000 (stop it with Ctrl+C)
#   make test      run every test with stand-in agents; no model is called
#   make lint      run the same ruff lint as CI (.github/workflows/ci.yml)
#
# Recipe lines must start with a TAB character, not spaces (a Makefile rule).

PY := .venv/bin/python

.PHONY: install run test lint

install:
	test -d .venv || uv venv --python 3.12 .venv
	uv pip install --python .venv -e ".[test]" -r requirements-dev.txt
	git config core.hooksPath scripts/git-hooks

run:
	$(PY) -m uvicorn backend.main:create_app --factory --reload --port 8000

test:
	$(PY) -m pytest -q

lint:
	.venv/bin/ruff check backend tests
