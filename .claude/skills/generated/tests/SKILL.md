---
name: tests
description: "Skill for the Tests area of jre-vidget. 25 symbols across 9 files."
---

# Tests

25 symbols | 9 files | Cohesion: 67%

## When to Use

- Working with code in `tests/`
- Understanding how test_output_dir_created, fake_batch, fake_download work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/test_engine.py` | fake_download, test_download_batch_never_raises_on_engine_error, test_download_batch_calls_on_result, on_result, test_fetch_info_maps_fields (+3) |
| `tests/test_cli.py` | test_download_success, test_download_failure_exits_1, _strip_ansi, test_download_help |
| `src/jre_vidget/models.py` | DownloadResult, BatchJob, DownloadError |
| `src/jre_vidget/engine.py` | download_batch, EngineError, fetch_info |
| `tests/test_integration.py` | test_output_dir_created, fake_batch |
| `tests/unit/test_properties_models.py` | _download_results, test_batch_job_counts_consistent |
| `tests/integration/test_youtube_cli.py` | test_download_without_publish_does_not_call_publisher |
| `tests/test_models.py` | test_batch_job_counts |
| `tests/unit/test_cli_preview.py` | test_preview_command_exits_1_on_error |

## Entry Points

Start here when exploring this area:

- **`test_output_dir_created`** (Function) — `tests/test_integration.py:40`
- **`fake_batch`** (Function) — `tests/test_integration.py:61`
- **`fake_download`** (Function) — `tests/test_engine.py:121`
- **`test_download_success`** (Function) — `tests/test_cli.py:38`
- **`test_download_failure_exits_1`** (Function) — `tests/test_cli.py:52`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `DownloadResult` | Class | `src/jre_vidget/models.py` | 231 |
| `BatchJob` | Class | `src/jre_vidget/models.py` | 244 |
| `EngineError` | Class | `src/jre_vidget/engine.py` | 52 |
| `DownloadError` | Class | `src/jre_vidget/models.py` | 86 |
| `test_output_dir_created` | Function | `tests/test_integration.py` | 40 |
| `fake_batch` | Function | `tests/test_integration.py` | 61 |
| `fake_download` | Function | `tests/test_engine.py` | 121 |
| `test_download_success` | Function | `tests/test_cli.py` | 38 |
| `test_download_failure_exits_1` | Function | `tests/test_cli.py` | 52 |
| `test_download_without_publish_does_not_call_publisher` | Function | `tests/integration/test_youtube_cli.py` | 393 |
| `test_batch_job_counts` | Function | `tests/test_models.py` | 30 |
| `test_download_batch_never_raises_on_engine_error` | Function | `tests/test_engine.py` | 101 |
| `test_download_batch_calls_on_result` | Function | `tests/test_engine.py` | 117 |
| `on_result` | Function | `tests/test_engine.py` | 126 |
| `test_batch_job_counts_consistent` | Function | `tests/unit/test_properties_models.py` | 190 |
| `download_batch` | Function | `src/jre_vidget/engine.py` | 417 |
| `test_fetch_info_maps_fields` | Function | `tests/test_engine.py` | 43 |
| `boom` | Function | `tests/test_engine.py` | 107 |
| `fetch_info` | Function | `src/jre_vidget/engine.py` | 209 |
| `test_download_returns_failed_on_error` | Function | `tests/test_engine.py` | 64 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Download → VideoFormat` | cross_community | 5 |
| `Download → _format_resolution` | cross_community | 5 |
| `Formats → VideoFormat` | cross_community | 5 |
| `Formats → _format_resolution` | cross_community | 5 |
| `Download → VideoInfo` | cross_community | 4 |
| `Formats → VideoInfo` | cross_community | 4 |
| `Download_batch → _ydl_format_for_config` | cross_community | 4 |
| `Download_batch → _extract_audio_postprocessor` | cross_community | 4 |
| `Download_batch → _merge_output_format` | cross_community | 4 |
| `Download_batch → _video_convert_postprocessor` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Jre_vidget | 8 calls |

## How to Explore

1. `gitnexus_context({name: "test_output_dir_created"})` — see callers and callees
2. `gitnexus_query({query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details
