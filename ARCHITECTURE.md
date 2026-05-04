# Architecture

## System Overview

`jre-vidget` is a local CLI tool that replaces iTube Studio for macOS video downloading.
It wraps yt-dlp (video extraction + format listing) and ffmpeg (stream merging / conversion)
and exposes them through a Typer CLI with a Rich terminal UI.

```
User → vidget CLI (cli.py mounts commands)
         ├── commands/*.py        → per-command Typer handlers
         ├── cli_common.py        → shared download/publish helpers, Rich Console(stderr=True)
         ├── engine.fetch_info()  → VideoInfo (formats, metadata)
         ├── engine.download()    → DownloadResult (filepath, status)
         ├── engine.download_batch() → BatchJob (per-URL results)
         └── config.AppConfig     → ~/.vidget/config.json
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
| `cli.py` | Typer app entry — mounts command groups (`config`, `auth`, `history`, …) and links to `commands/*` |
| `commands/*.py` | Individual commands (`download`, `batch`, `publish_cmd`, …) |
| `cli_common.py` | Shared CLI orchestration: `resolve_download_config`, progress session, publish-after-download, `gh workflow run` dispatch |
| `engine.py` | yt-dlp wrapper — pure business logic, no UI imports |
| `models.py` | Pydantic v2 data models for config, video info, results |
| `config.py` | `load_app_config` / `save_app_config` — JSON persistence to `~/.vidget/config.json` |
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
- CLI flags override persisted defaults when set; omitted options fall back to `AppConfig` (see `resolve_download_config` in `cli_common.py`)
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
| Human (default) | Rich-formatted text | stdlib logging (see `VIDGET_LOG_LEVEL` / `VIDGET_LOG_FORMAT`) and Rich progress |
| Machine (`--json`) | Pure JSON (one object) | Rich progress (when applicable), log lines, and plain-text error hints |

`cli_common.console` and Rich helpers use `Console(stderr=True)` so piping
`vidget ... --json` keeps **stdout** as a single JSON object for successful data commands.

**`vidget download … --json`** emits one JSON object shaped like the Pydantic payloads from
`emit_download_json_stdout` in `commands/download.py`: a **flat** top-level object with
`download` (always) and `publish` (only when `--publish` completed). There is no
`{ok, schemaVersion, data}` envelope.

Example (download + publish success):

```json
{
  "download": {
    "url": "https://example.com/watch",
    "status": "success",
    "filepath": "/Users/you/Downloads/video.mp4",
    "error": null,
    "duration_s": null,
    "finished_at": "2026-05-04T12:00:00"
  },
  "publish": {
    "video_id": "dQw4w9WgXcQ",
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "title": "My title",
    "privacy": "public",
    "removed_local_file": false
  }
}
```

`finished_at` and other datetimes are whatever Pydantic emits in JSON mode (typically
ISO-8601 strings with a timezone or offset); exact formatting can vary by field defaults.

On failure before JSON emission, the process exits non-zero; stderr carries the error
message (and optional JSON log lines if `VIDGET_LOG_FORMAT=json`).

## AI Decision Records

ADRs are stored in `docs/adr/` (index: `docs/adr/README.md`). Current records:

| ADR | Decision |
|-----|---------|
| ADR-001 | yt-dlp for extraction — maintained fork, site coverage |
| ADR-002 | Typer for CLI — typed commands, Rich-friendly |
| ADR-003 | Pydantic v2 for models — strict config and JSON |
| ADR-004 | ffmpeg-python for media helpers — typed wrapper over ffmpeg CLI |
| ADR-005 | Railway / Docker deployment notes (operational) |
