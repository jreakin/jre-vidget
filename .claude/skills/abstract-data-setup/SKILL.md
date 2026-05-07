---
name: abstract-data-setup
description: Set up or extend Abstract Data Starlight docs for jre-vidget. Docs live in docs-site/ with @abstractdata/starlight-theme; Python package in src/jre_vidget. Uses uv for Python, respects this repo’s Claude PostToolUse hooks and pre-commit. Use when the user says “set up docs”, “configure Abstract docs”, “wire Python autodoc”, “audit docstrings for docs”, “Starlight API reference”, or similar.
---

# Abstract Data — Set up docs (jre-vidget)

Bootstrap or extend documentation for **this repository** using `@abstractdata/starlight-theme`. The published npm package is **theme-only**; agent guidance lives here under `.claude/skills/abstract-data-setup/`.

## Repository facts (do not assume another layout)

| Item | Location |
|------|----------|
| Starlight app | `docs-site/` (`astro.config.mjs`, `src/content/docs/`) |
| Python package | `src/jre_vidget/` (import name `jre_vidget`) |
| Project metadata | `pyproject.toml` (`[project] name = "jre-vidget"`) |
| Deploy | `.github/workflows/deploy-web.yml` merges `web/dist` + `docs-site/dist` → GitHub Pages |
| Human setup doc | `docs/SETUP.md` (link from Starlight pages, do not duplicate wholesale) |

**Python commands:** use **`uv run`** (see AGENTS.md). Examples: `uv run interrogate …`, `uv run python -c "…"`. Do not rely on bare `python3` in instructions unless documenting a fallback.

**Monorepo hooks:** After **Edit**/**Write**, Claude Code runs the repo’s **PostToolUse** hooks (see below). Expect warnings when touching guarded paths; fix or acknowledge before finishing.

## Claude Code PostToolUse hooks (this repo)

Configured in `.claude/settings.json` (matcher **Edit|Write**). Scripts live under `.claude/hooks/`:

| Hook | Targets | Purpose |
|------|---------|---------|
| `no-print-check.sh` | `src/**/*.py` (excludes tests, `cli.py`, etc.) | No bare `print()` in production modules |
| `env-leak-check.sh` | Python under `src/` | Reduce accidental secret leakage |
| `domain-purity-check.sh` | `src/jre_vidget/engine.py` etc. | Keep engine free of UI imports |
| `sql-injection-check.sh` | Python | Safety scan for risky SQL patterns |
| `router-boundary-check.sh` | `src/jre_vidget/cli.py` | CLI delegates to engine/publisher |
| `composition-check.sh` | `web/src/**/*.tsx` | ≤8 `useState`, ≤300 LOC per file |
| `docs-starlight-frontmatter-check.sh` | `docs-site/src/content/docs/**/*.{md,mdx}` | Frontmatter + `title:` for Starlight |

Editing **`web/src/**/*.tsx`** triggers composition rules from AGENTS.md / `.cursor/rules/composition-rules.mdc`. Editing **`docs-site`** content triggers the Starlight frontmatter hook.

## When to invoke

- User asks to configure Abstract Data docs, Python autodoc, docstring audit, or Starlight API sections.
- Or `docs-site/package.json` lists `@abstractdata/starlight-theme` (this repo does).

If there is no `docs-site/` with Starlight, stop and tell the user to add the Starlight app first (see project history / `docs-site/README.md`).

## Workflow (phases)

Use clarifying questions when choices matter — do not assume module lists or branding overrides.

### Phase 1 — Confirm context

Read `docs-site/package.json` for `@abstractdata/starlight-theme`. Confirm `docs-site/astro.config.mjs` and `docs-site/src/content/docs/` exist. Announce findings briefly.

### Phase 2 — Locate the source project (jre-vidget default)

**Default:** Python source is the **repository root**: package path `src/jre_vidget/`. The docs project is **`docs-site/`** under the same root.

If the user’s cwd is `docs-site/`, the source tree is **`..`** (parent).  
Resolve **searchPath** for autodoc config as **`../src/jre_vidget`** relative to `docs-site/`, or absolute from repo root: `src/jre_vidget`.

### Phase 3 — Detect Python signals

Confirm `pyproject.toml`, `src/jre_vidget/__init__.py` (or package layout). Package name from `[project] name`: **`jre-vidget`**; import path **`jre_vidget`**.

Enumerate submodules under `src/jre_vidget/` (one level, cap ~30, skip dunders).

### Phase 4 — Audit docstring coverage

Prefer **`uv run interrogate`** when available (`uv sync --extra dev` includes dev tools; add `interrogate` to optional dev deps if missing — see Phase 10).

```bash
uv run interrogate -v src/jre_vidget --omit-covered-files --output json 2>/dev/null | jq .
```

If `interrogate` cannot run, fall back to a short AST walk via **`uv run python -c "..."`**.

Categorize modules: **≥80%** green, **50–79%** yellow, **<50%** red. Show a compact table.

### Phase 5 — Detect docstring style

Sample docstrings under `src/jre_vidget/`. Classify **Google / NumPy / Sphinx / mixed** using the marker patterns from the upstream Abstract Data skill. Report counts; if mixed, warn that generated API prose may be uneven until style is unified.

### Phase 6 — Modules to document

Offer choices: top-level package only, green-only, user-selected submodules, or everything (warn on red).

### Phase 7 — Brand / theme options

Read `docs-site/astro.config.mjs`. If `abstractData({ ... })` already sets `motion`, `credit`, `version`, only ask to change when the user wants updates.

Respect CI: **`ASTRO_SITE`** / **`ASTRO_BASE`** are set in **`deploy-web.yml`** for production builds — do not hardcode another base in the file without aligning deployment.

### Phase 8 — Write configs (autodoc pipeline)

This repository **already ships** the autodoc pipeline:

- `docs-site/scripts/build-python-docs.mjs` (uses `uv run pydoc-markdown` from the repo root)
- `docs-site/scripts/python-autodoc.json` — `searchPath` **`../src`**, `outputDir` **`src/content/docs/api`**, `modules` list for public packages
- `docs-site/package.json` — script **`docs:python`**
- `pydoc-markdown` in **`pyproject.toml`** (`[project.optional-dependencies] dev`)

**Edits to make when the API surface changes:** add or remove fully-qualified names in `python-autodoc.json` and re-run **`bun run docs:python`**. Keep the Starlight sidebar **`autogenerate: { directory: 'api' }`** in `astro.config.mjs` (do not duplicate).

### Phase 9 — Run generation

From repo root: `uv sync --extra dev` then `cd docs-site && bun run docs:python`. GitHub Actions runs the same before **Build docs (Starlight)** in `deploy-web.yml`.

### Phase 10 — Pre-commit: docstring coverage (source repo)

This repo already has **`.pre-commit-config.yaml`** (ruff, YAML checks, conventional commits). The **interrogate** hook targets **`src/jre_vidget`** with **`--fail-under=70`** (repo aggregate ~73% today); raise the threshold toward **80** as coverage improves.

**`interrogate`** is listed under **`[project.optional-dependencies] dev`** in `pyproject.toml`. Run **`uv sync --extra dev`** before **`uv run interrogate`**.

Do not duplicate hooks. Tell the user to run **`pre-commit install`** at the repo root if needed.

### Phase 11 — Summary

Summarize: configured paths, coverage breakdown, docstring style, theme options, files touched, generated page count (if any), and next steps (`bun dev` in `docs-site`, open `/docs/` on Pages URL **`/<repo>/docs/`**).

## Idempotency

- One `abstractData(...)` plugin in `astro.config.mjs`.
- No duplicate sidebar autogenerate blocks.
- Do not overwrite hand-written Starlight pages outside **`src/content/docs/api/`** unless the user asked.

## Out of scope here

- Replacing GitHub Pages merged deploy with another host (see DEPLOYMENTS.md).
- TypeDoc / OpenAPI pipelines (future Abstract Data rounds).

## Files this skill commonly reads / writes

**Reads:** `docs-site/package.json`, `docs-site/astro.config.mjs`, `pyproject.toml`, `src/jre_vidget/**`, `.pre-commit-config.yaml`, `.claude/settings.json` (for hook awareness).

**Writes:** `docs-site/scripts/python-autodoc.json`, edits to `docs-site/astro.config.mjs`, `docs-site/package.json`, optionally `.pre-commit-config.yaml` and `pyproject.toml` (with **`uv lock`**).

## Notes for the agent

- Align with **AGENTS.md** (scope, uv, no `ui` imports in `engine.py`).
- After editing Python or web TSX, hooks may fire — treat warnings as actionable.
- Keep **`docs-site`** MDX compatible with Starlight frontmatter (`title`, etc.) so **`docs-starlight-frontmatter-check.sh`** stays quiet.
