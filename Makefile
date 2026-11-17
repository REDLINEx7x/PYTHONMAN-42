PYTHON = uv run python
FILE = config.json

.PHONY: install run debug clean lint lint-strict

install:
	@uv sync

run:
	@$(PYTHON) main.py $(FILE)

debug:
	@$(PYTHON) -m pdb main.py $(FILE)

clean:
	@rm -rf __pycache__ .mypy_cache
	@find . -type d -name __pycache__ -exec rm -rf {} +

lint:
	@flake8 .
	@mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@flake8 .
	@mypy . --strict

.PHONY: install run debug clean lint lint-strict
