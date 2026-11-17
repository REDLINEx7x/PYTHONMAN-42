PYTHON = uv run python
FILE = config.json

.PHONY: install run debug clean lint lint-strict

install:
	@uv sync

run:
	@$(PYTHON) pac-man.py $(FILE)

debug:
	@$(PYTHON) -m pdb pac-man.py $(FILE)

clean:
	@rm -rf __pycache__ .mypy_cache
	@find . -type d -name __pycache__ -exec rm -rf {} +

lint:
	@uv run flake8 .
	@uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@uv run flake8 .
	@uv run mypy . --strict