# MEMORY.md
# Cap: 150 lines — clean after every 10 sessions
# Last Updated: 2026-05-04

## Current Task State

*Maintenance / docs / tests aligned with May 2026 assessment plans. Canonical agent guide: root `AGENTS.md`.*

---

## Completed Phases

Phases 1–16 (and follow-on prompts such as metadata preview / setup wizard) are implemented in-tree: Typer CLI, yt-dlp engine, YouTube auth + publisher, GitHub Actions workflows, Vite web UI on `gh-pages`, error reporting hooks, and bootstrap workflow. See `prompts/` for historical specs; trust `src/`, `web/src/`, and `.github/workflows/` as source of truth.

---

## Key Decisions Made

- Project type: CLI (`vidget`) + optional browser UI (`web/`) backed by GitHub Actions
- Package manager: uv; tests: pytest; types: ty; lint/format: ruff
- Entry point: `vidget = "jre_vidget.cli:app"`
- Config path: `~/.vidget/config.json`
- No async in the download engine — synchronous yt-dlp + publisher calls
- `engine.py` must never import `ui.py` (see `ARCHITECTURE.md`)

---

## Known Failure Patterns

- OAuth redirect port conflicts on shared machines → use `VIDGET_OAUTH_PORT` (see `.env.example` and `auth.py`).
- Stale GitNexus graph after large refactors → `npx gitnexus analyze` in repo root.

---

## Open Questions

*None tracked here — use issue tracker or Notion project page.*

---

## Compaction Instructions

When context reaches 80% usage:

1. Record the current task and last file touched under **Current Task State**
2. Note any failing tests or unresolved errors briefly
3. Discard raw tool transcripts — keep conclusions only
4. Preserve: phase status, open questions, failure patterns, key decisions
