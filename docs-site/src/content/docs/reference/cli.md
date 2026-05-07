---
title: CLI overview
description: Typer CLI entry points for agents and humans — nouns, verbs, --json, exit codes.
sidebar:
  order: 10
---

The `vidget` command is the primary interface. Install with `uv` from the repo root, then:

```bash
uv run vidget --help
uv run vidget download --help
uv run vidget --version
```

## Machine-readable output

Commands that return structured data support **`--json`**: stdout is JSON only; progress and Rich UI go to stderr so pipelines stay clean:

```bash
uv run vidget download "https://example.com/watch?v=…" --json
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General / unexpected failure |
| `2` | Usage / argument error |
| `3` | Authentication / permission |
| `4` | Transient — safe to retry |
| `5` | Conflict (e.g. file exists with `--no-overwrite`) |
| `130` | Interrupted (Ctrl-C) |

See **[SKILL.md](https://github.com/jreakin/jre-vidget/blob/main/SKILL.md)** in the repository for the full agent-oriented contract (flags, JSON shapes, exit codes).
