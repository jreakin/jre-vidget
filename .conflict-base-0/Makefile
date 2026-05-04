<<<<<<< New base: Project: add CLI stub, docs, Makefile, and packaging changes
.PHONY: setup update download batch formats install-cli \
        install dev test lint format typecheck format-check coverage check clean all

IMAGE := jre-vidget

# ---------------------------------------------------------------------------
# First-time setup and updates
# ---------------------------------------------------------------------------

# Build the Docker image — run this once after cloning
setup:
	docker build -t $(IMAGE) .
	@echo ""
	@echo "✓  $(IMAGE) is ready."
	@echo ""
	@echo "Usage:"
	@echo "   make download URL=\"https://video.foxnews.com/...\""
	@echo "   make batch    FILE=urls.txt"
	@echo "   make formats  URL=\"https://video.foxnews.com/...\""
	@echo ""
	@echo "Files land in ./downloads/ by default."
	@echo "Override with: make download URL=\"...\" OUTPUT=/your/path"
	@echo ""
	@echo "To use 'vidget' as a global command:"
	@echo "   make install-cli"

# Rebuild after pulling new changes (no layer cache)
update:
	docker build --no-cache -t $(IMAGE) .
	@echo "✓  $(IMAGE) updated."

# ---------------------------------------------------------------------------
# Download commands — Docker required, no Python/yt-dlp/ffmpeg on host
# ---------------------------------------------------------------------------

OUTPUT ?= $(PWD)/downloads

# Download a single video
# Usage: make download URL="https://..."
#        make download URL="https://..." OUTPUT=~/Videos
download:
	@test -n "$(URL)" || (echo "Error: URL is required\nUsage: make download URL=\"https://...\"" && exit 1)
	@mkdir -p "$(OUTPUT)"
	docker run --rm \
		-v "$(OUTPUT):/downloads" \
		$(IMAGE) download "$(URL)" --output /downloads

# Batch download from a text file (one URL per line, # for comments)
# Usage: make batch FILE=urls.txt
#        make batch FILE=urls.txt OUTPUT=~/Videos
batch:
	@test -n "$(FILE)" || (echo "Error: FILE is required\nUsage: make batch FILE=urls.txt" && exit 1)
	@mkdir -p "$(OUTPUT)"
	docker run --rm \
		-v "$(OUTPUT):/downloads" \
		-v "$(abspath $(FILE)):/urls.txt:ro" \
		$(IMAGE) batch /urls.txt --output /downloads

# List available formats for a URL (no download)
# Usage: make formats URL="https://..."
formats:
	@test -n "$(URL)" || (echo "Error: URL is required\nUsage: make formats URL=\"https://...\"" && exit 1)
	docker run --rm $(IMAGE) formats "$(URL)"

# Install bin/vidget as a global command so you can run `vidget` from anywhere
install-cli:
	ln -sf "$(PWD)/bin/vidget" /usr/local/bin/vidget
	@echo "✓  vidget installed → /usr/local/bin/vidget"

# ---------------------------------------------------------------------------
# Dev workflow (Python / uv)
# ---------------------------------------------------------------------------

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

# Lint (ruff + mypy)
lint:
	uv run ruff check src/ tests/
	uv run mypy src/ --strict

# Auto-format source
format:
	uv run ruff format src/ tests/

# Type check only
typecheck:
	uv run mypy src/ --strict

# Check formatting without modifying (used in CI)
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
|||||||
=======
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
>>>>>>> Current commit: Project: add CLI stub, docs, Makefile, and packaging changes
