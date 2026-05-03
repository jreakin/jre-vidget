.PHONY: install dev test lint format typecheck clean check all

# Install runtime dependencies
install:
	uv sync

# Install with dev dependencies
dev:
	uv sync --extra dev

# Run full test suite
test:
	uv run pytest

# Run unit tests only, stop on first failure
test-unit:
	uv run pytest tests/unit -x

# Run integration tests, verbose
test-integration:
	uv run pytest tests/integration -v

# Run tests with coverage report
coverage:
	uv run pytest --cov=src --cov-report=term-missing

# Lint (ruff check)
lint:
	uv run ruff check src/ tests/
	uv run mypy src/ --strict

# Auto-format source
format:
	uv run ruff format src/ tests/

# Type check only
typecheck:
	uv run mypy src/ --strict

# Check formatting without modifying files (used in CI)
format-check:
	uv run ruff format --check src/ tests/

# Pre-flight: verify yt-dlp and ffmpeg are available
check:
	uv run vidget check

# Remove build artifacts and caches
clean:
	rm -rf dist/ build/ .venv/ __pycache__/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -name "*.pyc" -delete
	find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

# Run all quality checks (CI equivalent)
all: format-check lint test
