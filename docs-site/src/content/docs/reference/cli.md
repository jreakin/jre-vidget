---
title: CLI overview
description: vidget commands, --json, headless behavior, and exit codes for humans and agents.
sidebar:
  order: 10
---

The **`vidget`** entry point is defined in `pyproject.toml` and implemented with Typer. Install from the repo root:

```bash
uv run vidget --help
uv run vidget download --help
uv run vidget config --help
uv run vidget auth --help
uv run vidget --version
```

## Command map

| Area | Commands |
|------|----------|
| Download | `download`, `batch`, `formats`, `preview` |
| Publish | `publish` (local or workflow-assisted flows depending on options) |
| Settings | `config show`, `config set`, `config reset` |
| YouTube auth | `auth login`, `auth status`, `auth logout`, `auth print-token` |
| Upload history | `history append` (used with CI / `uploads.json` workflows) |

Dependency checks (`yt-dlp`, ffmpeg warning) run for commands that need downloads unless you are only using `config`, `history`, or `auth` (see `cli.py` callback).

## `--json` and streams

Commands that emit structured results accept **`--json`**. Contract:

- **stdout** — pure JSON (pipe to `jq`, agents parse this).
- **stderr** — progress, logs, Rich UI (humans and troubleshooting).

Example:

```bash
uv run vidget download "https://example.com/watch?v=dQw4w9WgXcQ" --json
```

## Non-interactive / agents

In headless environments, destructive or confirm prompts are skipped or require explicit flags (see **`--yes`** / **`--no-confirm`** on relevant commands). Prefer **`--json`** for automation.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General / unexpected failure |
| `2` | Usage / argument error (Typer) |
| `3` | Authentication / permission |
| `4` | Transient — safe to retry |
| `5` | Conflict (e.g. existing file with `--no-overwrite`) |
| `130` | Interrupted (Ctrl+C) |

Full machine-oriented detail (JSON shapes, edge cases) lives in **[SKILL.md](https://github.com/jreakin/jre-vidget/blob/main/SKILL.md)** in the repository.
