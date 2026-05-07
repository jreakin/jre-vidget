---
title: Setup
description: Install jre-vidget and configure OAuth, secrets, and GitHub Pages.
sidebar:
  order: 2
---

## Quick install

Use [uv](https://docs.astral.sh/uv/) from the cloned repository:

```bash
uv sync
uv run vidget --help
```

For development tooling (tests, lint, typecheck):

```bash
uv sync --extra dev
```

## Full setup

OAuth client configuration, GitHub secrets for Actions, and GitHub Pages URLs are documented in the repo:

**[docs/SETUP.md](https://github.com/jreakin/jre-vidget/blob/main/docs/SETUP.md)**

Follow that guide so browser OAuth and workflow publishing match your fork’s URLs.
