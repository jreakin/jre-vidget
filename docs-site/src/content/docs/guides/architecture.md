---
title: Architecture
description: How the CLI, engine, UI, and publisher layers fit together in jre-vidget.
sidebar:
  order: 21
---

## Layers

| Layer | Role | Modules |
|-------|------|---------|
| **CLI** | Typer commands, `--json`, exit codes, dependency checks | `jre_vidget.cli`, `jre_vidget.commands.*`, `cli_common` |
| **Engine** | yt-dlp calls, batching, progress hooks — **no Rich/Typer** | `jre_vidget.engine` |
| **UI** | Rich panels, tables, spinners — **only from CLI** | `jre_vidget.ui` |
| **Publisher** | YouTube Data API uploads | `jre_vidget.publisher`, `publish_flow` |
| **Config / auth** | Disk config and OAuth helpers | `jre_vidget.config`, `jre_vidget.auth` |

**Rule:** `engine` must not import `ui` (see project rules). Human-facing output flows **CLI → ui**; automation uses **`--json`** on stdout.

## ADRs and prompts

Design decisions and phase specs live in the GitHub repo:

- **[docs/adr/](https://github.com/jreakin/jre-vidget/tree/main/docs/adr)** — architecture decision records
- **`prompts/phase-*`** — phased build specs (implementation reference)

## Docs site

This Starlight site (`docs-site/`) builds static HTML; API pages under **API Reference** are generated from docstrings via **`bun run docs:python`**.
