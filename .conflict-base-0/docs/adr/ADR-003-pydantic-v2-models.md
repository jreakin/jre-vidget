# ADR-003: Pydantic v2 for Data Models

**Date:** 2026-05-03
**Status:** Accepted

## Context

We needed a way to define, validate, and serialize all data passed between the CLI,
engine, and config layers (`VideoInfo`, `DownloadConfig`, `AppConfig`, `DownloadResult`,
`BatchJob`).

## Decision

Use Pydantic v2 (`pydantic>=2`) for all data models.

## Rationale

- **JSON serialization** — `model_dump_json()` / `model_validate_json()` for config
  persistence to `~/.vidget/config.json` with no extra code
- **Path support** — Pydantic v2 handles `Path` fields natively with `arbitrary_types_allowed`
- **Computed fields** — `@property` accessors (`duration_str`, `best_formats`,
  `output_template`) are clean and don't need `@computed_field` decoration for read-only use
- **Strict typing** — `mypy --strict` works cleanly with Pydantic v2 models
- Alternatives considered: `dataclasses` (no validation, no JSON), `attrs` (validation but
  less ergonomic JSON), raw dicts (no type safety)

## Consequences

- `model_config = {"arbitrary_types_allowed": True}` required on models that hold `Path`
- All models are immutable by default in v2; use `model_copy(update=...)` to modify
- `DownloadResult.finished_at` uses `Field(default_factory=datetime.now)` — Pydantic v2
  syntax, not v1's `default_factory=datetime.utcnow`

## Model Version

claude-sonnet-4-6
