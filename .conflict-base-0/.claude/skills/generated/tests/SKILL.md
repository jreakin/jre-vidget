---
name: tests
description: "Skill for the Tests area of jre-vidget. 12 symbols across 4 files."
---

# Tests

12 symbols | 4 files | Cohesion: 77%

## When to Use

- Working with code in `tests/`
- Understanding how test_batch_job_counts, test_download_batch_never_raises_on_engine_error, test_download_batch_calls_on_result work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/test_engine.py` | test_download_batch_never_raises_on_engine_error, test_download_batch_calls_on_result, fake_download, on_result, test_fetch_info_maps_fields (+1) |
| `src/jre_vidget/engine.py` | download_batch, EngineError, fetch_info |
| `src/jre_vidget/models.py` | DownloadResult, BatchJob |
| `tests/test_models.py` | test_batch_job_counts |

## Entry Points

Start here when exploring this area:

- **`test_batch_job_counts`** (Function) — `tests/test_models.py:30`
- **`test_download_batch_never_raises_on_engine_error`** (Function) — `tests/test_engine.py:75`
- **`test_download_batch_calls_on_result`** (Function) — `tests/test_engine.py:91`
- **`fake_download`** (Function) — `tests/test_engine.py:95`
- **`on_result`** (Function) — `tests/test_engine.py:100`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `DownloadResult` | Class | `src/jre_vidget/models.py` | 166 |
| `BatchJob` | Class | `src/jre_vidget/models.py` | 179 |
| `EngineError` | Class | `src/jre_vidget/engine.py` | 48 |
| `test_batch_job_counts` | Function | `tests/test_models.py` | 30 |
| `test_download_batch_never_raises_on_engine_error` | Function | `tests/test_engine.py` | 75 |
| `test_download_batch_calls_on_result` | Function | `tests/test_engine.py` | 91 |
| `fake_download` | Function | `tests/test_engine.py` | 95 |
| `on_result` | Function | `tests/test_engine.py` | 100 |
| `download_batch` | Function | `src/jre_vidget/engine.py` | 305 |
| `test_fetch_info_maps_fields` | Function | `tests/test_engine.py` | 42 |
| `boom` | Function | `tests/test_engine.py` | 81 |
| `fetch_info` | Function | `src/jre_vidget/engine.py` | 205 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Fetch_info → VideoFormat` | cross_community | 4 |
| `Fetch_info → _format_resolution` | cross_community | 4 |
| `Download_batch → _ydl_format_for_config` | cross_community | 4 |
| `Download_batch → _extract_audio_postprocessor` | cross_community | 4 |
| `Download_batch → _merge_output_format` | cross_community | 4 |
| `Download_batch → _video_convert_postprocessor` | cross_community | 4 |
| `Fetch_info → VideoInfo` | cross_community | 3 |
| `Download_batch → DownloadResult` | cross_community | 3 |
| `Download_batch → EngineError` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Jre_vidget | 5 calls |

## How to Explore

1. `gitnexus_context({name: "test_batch_job_counts"})` — see callers and callees
2. `gitnexus_query({query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details
