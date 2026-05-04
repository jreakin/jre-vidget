# Architecture

## System Overview

`jre-vidget` is a local CLI tool that replaces iTube Studio for macOS video downloading.
It wraps yt-dlp (video extraction + format listing) and ffmpeg (stream merging / conversion)
and exposes them through a Typer CLI with a Rich terminal UI.

```
User → vidget CLI (cli.py)
         ├── engine.fetch_info()   → VideoInfo (formats, metadata)
         ├── engine.download()     → DownloadResult (filepath, status)
         ├── engine.download_batch() → BatchJob (per-URL results)
         └── config.AppConfig      → ~/.vidget/config.json
                 ↓
           yt-dlp (subprocess / Python API)
                 ↓
           ffmpeg (via ffmpeg-python, for HLS merge)
                 ↓
           output file on disk
```

## Module Responsibilities

| Module | Purpose |
|--------|---------|
| `cli.py` | Typer app, all command handlers, Rich UI calls |
| `engine.py` | yt-dlp wrapper — pure business logic, no UI imports |
| `models.py` | Pydantic v2 data models for config, video info, results |
| `config.py` | AppConfig — JSON persistence to `~/.vidget/config.json` |
| `ui.py` | Rich UI functions — spinner, progress bar, tables |
| `checks.py` | Pre-flight: verify yt-dlp importable + ffmpeg on PATH |

## Key Architectural Constraint

**`engine.py` must never import from `ui.py`.**
The engine is testable in isolation. UI concerns belong entirely in `cli.py`.

## Data Flow

```
CLI arg → DownloadConfig (Pydantic) → engine.download()
                                            ↓
                                      yt-dlp options dict
                                            ↓
                                      progress_hook → Rich Progress bar
                                            ↓
                                      DownloadResult (filepath, status, error)
                                            ↓
                                      ui.print_result()
```

## Orchestration Pattern

Single-process CLI. No agents, no async, no background workers.
Each command is synchronous: validate → fetch info → download → print result.

Batch mode (`vidget batch urls.txt`) iterates URLs sequentially, capturing
results in a `BatchJob` and printing a summary table at the end.

## Retry Pattern

`engine.download()` accepts a `retries: int = 2` parameter.
On `DownloadError`, it backs off 2 seconds between attempts and logs each retry.
After exhausting retries, returns `DownloadResult(status=FAILED, error=...)` — never raises.

## Config Management

- Config stored at `~/.vidget/config.json`
- Loaded with `jre_vidget.config.load_app_config()` (returns `AppConfig` defaults if the file is missing)
- Saved with `jre_vidget.config.save_app_config(cfg)` (writes JSON with plaintext OAuth fields where set; not a raw `model_dump_json()` so secrets persist readably)
- CLI flags override persisted defaults when set; omitted options fall back to `AppConfig` (see `_resolve_download_config` in `cli.py`)
- `vidget config reset --yes` deletes the file

## Error Handling

| Error Type | Handler | Exit Code |
|------------|---------|-----------|
| Missing yt-dlp | `checks.py` → print install hint → exit | `1` |
| Missing ffmpeg | `checks.py` → print warning (non-fatal) | `0` |
| Download failure (permanent) | `engine.download()` → retry → `DownloadResult(FAILED)` | `1` |
| Download failure (transient / timeout) | `engine.download()` → retry exhausted | `4` |
| Auth / permission error | `engine.download()` → `DownloadResult(FAILED, auth_error=True)` | `3` |
| File already exists + `--no-overwrite` | `cli.py` conflict check | `5` |
| Bad output path | `_validate_output()` in cli.py → `ui.print_error()` | `1` |
| Bad arguments / missing flags | Typer automatic | `2` |
| Ctrl-C | `KeyboardInterrupt` handler in cli.py | `130` |

## Output Mode

`vidget` supports two output modes, selected per-command with `--json`:

| Mode | stdout | stderr |
|------|--------|--------|
| Human (default) | Rich-formatted text | structlog / warnings |
| Machine (`--json`) | Pure JSON (one object) | Rich progress + structlog |

The `Console(stderr=True)` instance in `ui.py` handles all progress/spinner output so
that piping `vidget ... --json` always produces parse-clean stdout.

JSON response shape:
```json
// success
{"ok": true, "schemaVersion": 1, "data": {...}}

// failure  
{"ok": false, "schemaVersion": 1, "error": {"code": "download_failed", "message": "...", "retryable": false}}
```

## AI Decision Records

ADRs are stored in `docs/adr/`. Current records:

| ADR | Decision |
|-----|---------|
| ADR-001 | yt-dlp over youtube-dl — actively maintained, Brightcove/HLS support |
| ADR-002 | Typer over Click — native Rich integration, cleaner type-annotated API |
| ADR-003 | Pydantic v2 for models — JSON serialization, validators, strict types |
| ADR-004 | ffmpeg-python over subprocess — typed wrapper, cleaner pipeline syntax |
