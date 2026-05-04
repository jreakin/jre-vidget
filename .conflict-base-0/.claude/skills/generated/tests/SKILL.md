---
name: tests
description: "Skill for the Tests area of jre-vidget. 18 symbols across 6 files."
---

# Tests

18 symbols | 6 files | Cohesion: 72%

## When to Use

- Working with code in `tests/`
- Understanding how test_batch_job_counts, test_download_batch_never_raises_on_engine_error, test_download_batch_calls_on_result work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/test_engine.py` | test_download_batch_never_raises_on_engine_error, test_download_batch_calls_on_result, on_result, fake_download, test_fetch_info_maps_fields (+1) |
| `tests/test_cli.py` | test_download_success, test_download_failure_exits_1, _strip_ansi, test_download_help |
| `src/jre_vidget/engine.py` | download_batch, EngineError, fetch_info |
| `src/jre_vidget/models.py` | BatchJob, DownloadResult |
| `tests/test_integration.py` | test_output_dir_created, fake_batch |
| `tests/test_models.py` | test_batch_job_counts |

## Entry Points

Start here when exploring this area:

- **`test_batch_job_counts`** (Function) — `tests/test_models.py:30`
- **`test_download_batch_never_raises_on_engine_error`** (Function) — `tests/test_engine.py:101`
- **`test_download_batch_calls_on_result`** (Function) — `tests/test_engine.py:117`
- **`on_result`** (Function) — `tests/test_engine.py:126`
- **`download_batch`** (Function) — `src/jre_vidget/engine.py:325`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `BatchJob` | Class | `src/jre_vidget/models.py` | 180 |
| `DownloadResult` | Class | `src/jre_vidget/models.py` | 167 |
| `EngineError` | Class | `src/jre_vidget/engine.py` | 49 |
| `test_batch_job_counts` | Function | `tests/test_models.py` | 30 |
| `test_download_batch_never_raises_on_engine_error` | Function | `tests/test_engine.py` | 101 |
| `test_download_batch_calls_on_result` | Function | `tests/test_engine.py` | 117 |
| `on_result` | Function | `tests/test_engine.py` | 126 |
| `download_batch` | Function | `src/jre_vidget/engine.py` | 325 |
| `test_output_dir_created` | Function | `tests/test_integration.py` | 40 |
| `fake_batch` | Function | `tests/test_integration.py` | 61 |
| `fake_download` | Function | `tests/test_engine.py` | 121 |
| `test_download_success` | Function | `tests/test_cli.py` | 38 |
| `test_download_failure_exits_1` | Function | `tests/test_cli.py` | 52 |
| `test_fetch_info_maps_fields` | Function | `tests/test_engine.py` | 43 |
| `boom` | Function | `tests/test_engine.py` | 107 |
| `fetch_info` | Function | `src/jre_vidget/engine.py` | 206 |
| `test_download_help` | Function | `tests/test_cli.py` | 21 |
| `_strip_ansi` | Function | `tests/test_cli.py` | 17 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Formats → VideoFormat` | cross_community | 5 |
| `Formats → _format_resolution` | cross_community | 5 |
| `Formats → VideoInfo` | cross_community | 4 |
| `Download_batch → _ydl_format_for_config` | cross_community | 4 |
| `Download_batch → _extract_audio_postprocessor` | cross_community | 4 |
| `Download_batch → _merge_output_format` | cross_community | 4 |
| `Download_batch → _video_convert_postprocessor` | cross_community | 4 |
| `Formats → EngineError` | cross_community | 3 |
| `Download_batch → _emit_retry_log` | cross_community | 3 |
| `Download_batch → DownloadResult` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Jre_vidget | 5 calls |

## How to Explore

1. `gitnexus_context({name: "test_batch_job_counts"})` — see callers and callees
2. `gitnexus_query({query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details
