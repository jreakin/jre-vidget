# ADR-002: Typer as CLI Framework

**Date:** 2026-05-03
**Status:** Accepted

## Context

We needed a CLI framework to expose `download`, `batch`, `formats`, and `config` commands
with typed options, help text, and shell completion.

## Decision

Use `typer[all]` (Typer with all extras, which includes Rich integration).

## Rationale

- **Native Rich integration** — `typer[all]` bundles `rich-click` for pretty help panels;
  no extra wiring needed
- **Type-annotated API** — commands are plain Python functions with annotated parameters;
  no decorator soup or manual `add_argument` calls
- **Subcommand support** — `app.add_typer(config_app, name="config")` is clean and testable
- **CliRunner** — Typer's `testing.CliRunner` makes integration tests trivial
- Alternatives considered: `click` (more boilerplate, no Rich integration out of box),
  `argparse` (stdlib but verbose), `fire` (no type safety, no subcommands)

## Consequences

- `typer[all]` pulls in `rich` and `shellingham` as dependencies — acceptable for a CLI tool
- Typer's subcommand architecture (nested `Typer` instances) means `config_app` must be
  added before `app` is invoked; order matters in `cli.py`
- `no_args_is_help=True` is set on the root app so bare `vidget` shows help

## Model Version

claude-sonnet-4-6
