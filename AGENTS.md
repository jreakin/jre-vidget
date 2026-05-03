# AGENTS.md
# Version: 0.1.0
# Last Updated: 2026-05-03
# Environment: dev
# Model: claude-sonnet-4-6
# Fallback Model: claude-haiku-4-5-20251001
# Project: jre-vidget
# Maintainer: jreakin

You are an expert Python software engineer working on **jre-vidget** — a CLI video downloader
that replaces iTube Studio. It wraps yt-dlp for video extraction and ffmpeg for format
conversion, exposed through a Typer CLI with a Rich terminal UI.

---

## Agent Scope

```
Reads:    src/, tests/, prompts/, docs/, .env.example, pyproject.toml
Writes:   src/, tests/, docs/
Executes: uv, ruff, pytest, mypy, git (feature branches only)
Off-limits: .env, ~/.vidget/config.json (user data), any other repository
```

---

## Project Structure

```
jre-vidget/
├── src/jre_vidget/
│   ├── __init__.py
│   ├── cli.py        # Typer app — entry point for `vidget` command
│   ├── engine.py     # yt-dlp wrapper — fetch_info, download, download_batch
│   ├── models.py     # Pydantic v2 data models
│   ├── config.py     # AppConfig — persists to ~/.vidget/config.json
│   ├── ui.py         # Rich UI — spinner, progress bar, tables, panels
│   └── checks.py     # Dependency pre-flight (yt-dlp + ffmpeg)
├── tests/
│   ├── unit/         # Pure unit tests (no network, no real yt-dlp)
│   └── integration/  # Full-stack tests with mocked yt-dlp
├── prompts/          # Phase-build prompts for AI coding agents
│   ├── phase-1-project-scaffold/
│   ├── phase-2-pydantic-models/
│   ├── phase-3-download-engine/
│   ├── phase-4-typer-cli/
│   ├── phase-5-rich-ui/
│   └── phase-6-config-error-polish/
├── docs/adr/         # AI Decision Records
├── SKILL.md          # Agent workflow guide (capabilities, exit codes, JSON shapes)
└── Makefile          # Standard dev entrypoints (make test, make lint, make install)
```

---

## Phase Build Order

**Always implement phases in order.** Each phase depends on the previous:

| Phase | Prompt | Deliverable |
|-------|--------|-------------|
| 1 | `prompts/phase-1-project-scaffold/current.md` | pyproject.toml, folder structure, stub cli.py |
| 2 | `prompts/phase-2-pydantic-models/current.md` | models.py (all data models) |
| 3 | `prompts/phase-3-download-engine/current.md` | engine.py (yt-dlp wrapper) |
| 4 | `prompts/phase-4-typer-cli/current.md` | cli.py (all commands) |
| 5 | `prompts/phase-5-rich-ui/current.md` | ui.py (Rich UI functions) |
| 6 | `prompts/phase-6-config-error-polish/current.md` | checks.py, retries, --version, install.sh |

**To implement a phase:** Read `current.md` in the phase directory before writing any code.
**To update a prompt:** Create a new `v{X.Y.Z}.md`, copy it to `current.md`, append to `CHANGELOG.md`.

---

## Commands You Must Know

```bash
uv sync                          # Install/sync dependencies
uv sync --extra dev              # With dev dependencies
uv run vidget --help             # Verify CLI entry point
uv run vidget --version          # Check version
uv run pytest                    # Run all tests
uv run pytest tests/unit -x      # Stop on first failure
uv run pytest -v --cov=src       # Run with coverage report
uv run ruff check src/           # Lint
uv run ruff format src/          # Format
uv run mypy src/ --strict        # Type check
```

---

## Architecture Notes

- **No imports from `ui.py` in `engine.py`** — the engine is pure business logic. All Rich
  UI lives in `ui.py` and is called only from `cli.py`.
- **No bare `print()` in `src/`** (except `cli.py` which uses `console.print` from Rich).
  Use `structlog` for all logging in engine and config modules.
- **Pydantic v2 throughout** — all data models inherit from `BaseModel`, use `model_dump_json`
  / `model_validate_json` for serialization.
- **Entry point:** `vidget = "jre_vidget.cli:app"` in pyproject.toml. The `app` object
  is the Typer application instance.

---

## Agentic CLI Design Principles

jre-vidget is a CLI tool designed to be invoked by AI coding agents as well as humans.
The following requirements are non-negotiable for agent compatibility.

### Exit Codes

Every command must exit with a meaningful code. Agents use exit codes for retry logic
and branching — never exit with a non-zero code for a success condition.

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General / unexpected failure |
| `2` | Usage / argument error (Typer handles this automatically) |
| `3` | Authentication / permission error |
| `4` | Transient error — safe to retry (network timeout, rate limit) |
| `5` | Conflict — file already exists and `--no-overwrite` is set |
| `130` | Interrupted by Ctrl-C (SIGINT) |

These codes are the **primary control flow mechanism** for agents. Map every error path
to the correct code.

### `--json` Flag — Machine-Readable Output

Every command that produces data output must support `--json`:

```python
# In cli.py — every data command follows this pattern
@app.command()
def download(url: str, ..., json_output: bool = typer.Option(False, "--json")):
    result = engine.download(config)
    if json_output:
        # stdout = pure JSON only — no Rich decorations
        print(result.model_dump_json())
    else:
        # stderr = progress/spinners (Rich goes to stderr via Console(stderr=True))
        # stdout = human-readable Rich output
        ui.print_result(result)
```

**API contract:** `stdout = data only; stderr = logs, progress, warnings`

When `--json` is active: Rich spinners and progress bars go to `stderr`
(use `Console(stderr=True)` for progress output), and `stdout` contains only the JSON
payload. This separation is what makes `vidget download URL --json | jq .status` work.

### Non-Interactive Mode / TTY Detection

Agents cannot respond to confirmation prompts. All write/destructive commands must:
- Accept `--yes` / `--no-confirm` to skip confirmation
- Auto-detect non-TTY (`sys.stdin.isatty()`) and skip prompts automatically
- Error immediately with clear missing-flag message if required args absent in headless mode

```python
import sys

def _is_headless() -> bool:
    return not sys.stdin.isatty()

# In commands that prompt:
if not yes and not _is_headless():
    confirm = typer.confirm("Overwrite existing file?")
    if not confirm:
        raise typer.Exit(0)
elif not yes and _is_headless():
    # headless with no --yes: proceed (for non-destructive) or abort (for destructive)
    pass
```

### Command Grammar

Use **noun → verb** hierarchy consistently — agents recognize this pattern from tools
like `gh pr create`, `kubectl pod get`, and `docker container ls`:

```
vidget download <url>          # not: vidget get-video
vidget batch <file>            # not: vidget batch-download
vidget config show             # not: vidget show-config
vidget config set <k> <v>      # not: vidget set-config
vidget config reset            # not: vidget reset-config
```

### Self-Documenting Help

Every command must have:
- A clear one-line description (used by agents during discovery)
- Required vs. optional flags labeled explicitly
- At least one realistic `--help` example using `rich_help_panel` or epilog
- The `--json` flag documented in every command's help text

---

## Definition of Done

A task is complete when **all** of the following are true:

### ✅ Code Quality
- [ ] All tests pass (`uv run pytest`)
- [ ] No linting errors (`uv run ruff check src/`)
- [ ] No formatting violations (`uv run ruff format --check src/`)
- [ ] Type hints on all public functions (`uv run mypy src/ --strict`)

### ✅ Documentation Hygiene
- [ ] Phase prompt acceptance criteria satisfied
- [ ] Any architectural decisions recorded in `docs/adr/`

### ✅ Safety & Security
- [ ] No secrets or credentials in committed code
- [ ] No bare `print()` in production modules (engine, models, config, checks)
- [ ] No `eval()` or `exec()` with user input

---

## Core Standards

### Naming Conventions

| Type | Convention | Examples |
|------|------------|---------|
| Functions/variables | `snake_case` | `fetch_info`, `output_dir` |
| Classes | `PascalCase` | `DownloadConfig`, `VideoInfo` |
| Constants | `UPPER_SNAKE_CASE` | `CONFIG_PATH`, `MAX_RETRIES` |
| Private methods | `_leading_underscore` | `_validate_output`, `_resolve` |
| Enums | `PascalCase` members | `Quality.HIGH`, `DownloadStatus.SUCCESS` |

### Python Patterns

```python
# ✅ GOOD — type hints, explicit errors, context managers
def download(
    config: DownloadConfig,
    progress_hook: ProgressHook | None = None,
    retries: int = 2,
) -> DownloadResult:
    """Download a video and return structured result."""
    if not config.url:
        raise ValueError("url is required")
    ...

# ❌ BAD — no types, swallowed errors
def download(config, hook=None):
    try:
        ...
    except:
        return None
```

### ✅ ALWAYS DO
- Type hints on every function signature
- Docstrings on all public functions
- Write tests for new features (mock yt-dlp at the boundary)
- Run `ruff format` before committing

### ⚠️ ASK FIRST
- Adding new dependencies (`uv add`)
- Changing CLI command signatures (breaks existing users)

### 🚫 NEVER DO
- Import `ui.py` from `engine.py`
- Call bare `print()` in `engine.py`, `models.py`, `config.py`, or `checks.py`
- Hardcode file paths — use `Path.home() / ".vidget"` pattern
- Swallow exceptions with bare `except:`

---

## Git Workflow

```
feat: add format selection to download command
fix: handle missing ffmpeg gracefully in checks
refactor: extract _validate_output helper to cli.py
test: add unit tests for DownloadConfig model
docs: update README with install instructions
```

---

## Conflict Resolution

When concerns compete:
1. **Correctness** (correct output) > **Performance** > **Style**
2. Type safety and Pydantic validation > convenience shortcuts
3. Clear error messages to the user > terse internal code

---

## Execution Sequence (for multi-step tasks)

Before beginning work on a multi-step task, explicitly state:
1. Which phase prompt applies
2. Which acceptance criteria must be met
3. Which modules will be touched
4. Validation command to run at the end
