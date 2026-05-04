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
- Loaded lazily by `AppConfig.load()` classmethod
- Saved via `AppConfig.save()` using `model_dump_json()`
- CLI flags always override config values (`_resolve(cli_value, config_value)`)
- `vidget config reset --yes` deletes the file

## Error Handling

| Error Type | Handler |
|------------|---------|
| Missing yt-dlp | `checks.py` → print install hint → exit(1) |
| Missing ffmpeg | `checks.py` → print warning (non-fatal) |
| Download failure | `engine.download()` → retry → `DownloadResult(FAILED)` |
| Bad output path | `_validate_output()` in cli.py → `ui.print_error()` → exit(1) |
| Ctrl-C | `KeyboardInterrupt` handler in cli.py → exit(130) |

## AI Decision Records

ADRs are stored in `docs/adr/`. Current records:

| ADR | Decision |
|-----|---------|
| ADR-001 | yt-dlp over youtube-dl — actively maintained, Brightcove/HLS support |
| ADR-002 | Typer over Click — native Rich integration, cleaner type-annotated API |
| ADR-003 | Pydantic v2 for models — JSON serialization, validators, strict types |
| ADR-004 | ffmpeg-python over subprocess — typed wrapper, cleaner pipeline syntax |
