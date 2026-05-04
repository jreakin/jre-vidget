# AGENTS.md
# Version: 0.1.0
# Last Updated: 2026-05-04
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
Reads:    src/, tests/, prompts/, docs/, web/, worker/, .env.example, pyproject.toml
Writes:   src/, tests/, docs/, web/src/, worker/src/
Executes: uv, ruff, pytest, ty, git (feature branches only)
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
│   ├── models.py     # Pydantic v2 data models (incl. YouTube publish models)
│   ├── config.py     # AppConfig — persists to ~/.vidget/config.json
│   ├── ui.py         # Rich UI — spinner, progress bar, tables, panels
│   ├── checks.py     # Dependency pre-flight (yt-dlp + ffmpeg)
│   ├── auth.py       # YouTube OAuth2 — get_credentials(), VIDGET_* env var support
│   └── publisher.py  # YouTube Data API v3 upload wrapper — upload()
├── tests/
│   ├── unit/         # Pure unit tests (no network, no real yt-dlp or YouTube API)
│   └── integration/  # Full-stack tests with mocked yt-dlp
├── web/              # Vite + React + TanStack browser UI (deployed to gh-pages)
│   ├── src/          # TypeScript source — components, pages, api/, hooks/
│   ├── dist/         # Built output (committed, served by GitHub Pages)
│   └── package.json
├── prompts/          # Phase-build prompts for AI coding agents
│   ├── phase-1-project-scaffold/
│   ├── phase-2-pydantic-models/
│   ├── phase-3-download-engine/
│   ├── phase-4-typer-cli/
│   ├── phase-5-rich-ui/
│   ├── phase-6-config-error-polish/
│   ├── phase-7-youtube-models/
│   ├── phase-8-youtube-auth/
│   ├── phase-9-youtube-publisher/
│   ├── phase-10-youtube-cli/
│   ├── phase-11-actions-workflow/
│   ├── phase-12-web-ui/
│   ├── phase-13-error-reporting/
│   └── phase-14-bootstrap-workflow/
├── .github/workflows/  # CI + publish + deploy-web + bootstrap workflows
├── docs/adr/           # Architecture Decision Records
├── docs/SETUP.md       # Cloner setup guide — OAuth, secrets, GitHub Pages
├── uploads.json        # Upload history (appended by publish.yml workflow)
├── SKILL.md            # Agent workflow guide (capabilities, exit codes, JSON shapes)
└── Makefile            # Standard dev entrypoints (make test, make lint, make install)
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
| 7 | `prompts/phase-7-youtube-models/current.md` | AuthConfig, PublishConfig, PublishResult in models.py |
| 8 | `prompts/phase-8-youtube-auth/current.md` | auth.py — OAuth2 get_credentials(), env var overrides |
| 9 | `prompts/phase-9-youtube-publisher/current.md` | publisher.py — resumable YouTube upload |
| 10 | `prompts/phase-10-youtube-cli/current.md` | `vidget download --publish` CLI command |
| 11 | `prompts/phase-11-actions-workflow/current.md` | publish.yml workflow + VIDGET_REFRESH_TOKEN env var |
| 12 | `prompts/phase-12-web-ui/current.md` | Vite + React browser UI on gh-pages |
| 13 | `prompts/phase-13-error-reporting/current.md` | Automated error reporting + ErrorBoundary |
| 14 | `prompts/phase-14-bootstrap-workflow/current.md` | bootstrap.yml — scaffold secrets/variables for cloners |

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
uv run ty check src/ tests/      # Type check (ty replaces mypy)
```

---

## Architecture Notes

- **No imports from `ui.py` in `engine.py`** — the engine is pure business logic. All Rich
  UI lives in `ui.py` and is called only from `cli.py`.
- **No bare `print()` in `src/`** (except `cli.py` which uses `console.print` from Rich).
  Use the standard library **`logging`** for program diagnostics in modules that are not the Rich CLI surface (for example `logging.getLogger(__name__)` in `engine.py`). Human-facing output stays on Rich via `cli.py` / `ui.py`. **`structlog` is not a project dependency** today; do not introduce it without an explicit decision and an ADR — the previous structlog-only wording was outdated.
- **Dependency versions (`yt-dlp` and peers):** `pyproject.toml` uses **lower bounds** (e.g. `yt-dlp>=2024.1.1`) so extractor fixes and compatible releases flow in when you run `uv lock` / `uv sync`. **Upper bounds (version ceilings)** trade upstream surprises against delayed security or bugfix picks until the range is widened; do not add ceilings in drive-by changes. If you propose a ceiling (for example to cap `yt-dlp` during a known regression window), do it in a dedicated change with maintainer agreement and a short rationale in the PR.
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
- [ ] Type hints on all public functions (`uv run ty check src/`)

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

---

## Web UI — Component Composition Rules

The `web/` sub-project is a Vite + React + TypeScript SPA. These rules apply to all `.tsx` and
`.ts` files under `web/src/`.

### Hard Thresholds

| Rule | Limit | Action when exceeded |
|------|-------|----------------------|
| `useState` hooks per component | ≤ 8 | Extract to custom hook |
| Lines of code per component | ≤ 300 | Split into sub-components |
| Form field `useState` | ≤ 4 | Use `useFormReducer` |

### Required Shared Hooks (`web/src/hooks/`)

Before creating a new state pattern, check `web/src/hooks/README.md`. Use canonical hooks:

| Hook | When to use |
|------|------------|
| `useAsyncState<T>` | Any loading/error/data triplet |
| `useFormReducer<T>` | 5–8 form fields with optional Zod validation |
| `useTableFilters<T>` | Filter, sort, paginate any collection |
| `useModal<T>` | Open/close/data for any modal dialog |

### Form State Decision Tree

```
1–4 fields     → useState
5–8 fields     → useFormReducer (web/src/hooks/use-form-reducer.ts)
>8 fields      → React Hook Form + Zod
```

### Error UI Requirement

Every `catch` block in React components **must** render `<ErrorDisplay message={...} />`.
Silent `console.error` with no UI feedback is a bug.

```tsx
// ✅ CORRECT
} catch (err) {
  setError(err instanceof Error ? err.message : 'Unknown error')
}
// …
{error && <ErrorDisplay message={error} onRetry={refetch} />}

// ❌ WRONG
} catch (err) {
  console.error(err)  // user sees nothing
}
```

### TypeScript Discipline

- No `any` — use `unknown` and narrow with type guards
- `as` assertions require a `// SAFETY:` comment explaining why narrowing isn't possible
- Never `as unknown as T`
- Explicit return types on all async functions

### Tailwind DRY Rule

Extract repeated Tailwind class combinations to `@layer components` in `web/src/index.css`
after they appear in 3+ places.

### Hook Index

Always keep `web/src/hooks/README.md` current. Add a row whenever a hook is added,
renamed, or removed.

---

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **jre-vidget** (1755 symbols, 2906 relationships, 76 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/jre-vidget/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/jre-vidget/context` | Codebase overview, check index freshness |
| `gitnexus://repo/jre-vidget/clusters` | All functional areas |
| `gitnexus://repo/jre-vidget/processes` | All execution flows |
| `gitnexus://repo/jre-vidget/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

---

## Learned User Preferences

- Phase work is often kicked off by referencing a phase prompt (for example `@phase-4-typer-cli.md Implement` or `@phase-15-metadata-preview Implement`, with or without the `.md` suffix) instead of restating full acceptance criteria.

## Learned Workspace Facts

- A root-level `tmp/` directory is used for local CLI or download smoke tests; `tmp/` is listed in `.gitignore` so artifacts stay out of version control.
- Public GitHub path used for badges and workflow links in docs is `jreakin/jre-vidget`.
- Phase 15 (metadata preview and optional URL-based `publish` via GitHub Actions) is documented under `prompts/phase-15-metadata-preview/`; read `current.md` there before implementing, like earlier numbered phases.

---

## Notion References

- Tasks DB: collection://2e97d7f5-6298-80a5-acef-000bb9796a9d
- Project Page: https://www.notion.so/3567d7f5629881f5bd21e5cbafbab309
- Client Page: https://www.notion.so/2f37d7f5629881bb814de76479af10db
