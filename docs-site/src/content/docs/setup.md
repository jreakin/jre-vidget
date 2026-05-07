---
title: Setup
description: Install jre-vidget, dependencies, OAuth, GitHub Actions, and GitHub Pages.
sidebar:
  order: 2
---

## Prerequisites

- **Python 3.11+** (project requirement).
- **[uv](https://docs.astral.sh/uv/)** recommended for installs and `uv run vidget …`.
- **ffmpeg** on `PATH` for merging streams and format conversion. Without it, installs succeed but the CLI warns and conversion may fail — install via your OS package manager (e.g. `brew install ffmpeg` on macOS).

## Quick install

From a clone of the repository:

```bash
uv sync
uv run vidget --help
uv run vidget --version
```

Development tooling (tests, lint, typecheck, doc generators):

```bash
uv sync --extra dev
```

## Defaults and config file

Preferences default to sensible paths (for example output under your home directory). The CLI persists settings under **`~/.vidget/config.json`** — see the **`config`** subcommands (`vidget config show`, `set`, `reset`) and the API docs for `AppConfig`.

## OAuth, CI secrets, and Pages URLs

Browser OAuth, GitHub Actions secrets (`VIDGET_*`), and exact GitHub Pages / OAuth redirect URLs must match **your** fork and Google Cloud OAuth client. Follow the repo guide:

**[docs/SETUP.md](https://github.com/jreakin/jre-vidget/blob/main/docs/SETUP.md)**

Published docs from this Starlight site typically appear at:

`https://<user>.github.io/<repo>/docs/`

The React UI may live at `https://<user>.github.io/<repo>/` on the same deployment — ensure OAuth **Authorized JavaScript origins** and **redirect URIs** include those URLs.

## Regenerate API docs locally

After changing Python modules listed in `docs-site/scripts/python-autodoc.json`:

```bash
uv sync --extra dev
cd docs-site && bun run docs:python
```

Then run `bun run dev` to preview.
