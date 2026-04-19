.PHONY: install install-hooks lint format test check all clean

# Install uv dev dependencies at the root level
install:
	uv sync

# Install pre-commit hooks into the local git repo
install-hooks: install
	uv run pre-commit install

# Run ruff linter across all Python files
lint:
	uv run ruff check .

# Run ruff formatter across all Python files
format:
	uv run ruff format .

# Run the manifest validation tests
test:
	uv run pytest test_samples_coverage.py -v

# Run all pre-commit hooks against all files
check:
	uv run pre-commit run --all-files

# Full setup: install deps + hooks
setup: install install-hooks

# Full CI-like check: lint + format check + tests
all: check test

# Remove root .venv (does not touch per-sample .venvs)
clean:
	rm -rf .venv .pytest_cache .ruff_cache
