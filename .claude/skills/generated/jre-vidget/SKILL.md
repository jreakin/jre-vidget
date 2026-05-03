<<<<<<< New base: Add GitNexus docs, Typer CLI, and Rich UI
---
name: jre-vidget
description: "Skill for the Jre_vidget area of jre-vidget. 57 symbols across 7 files."
---

# Jre_vidget

57 symbols | 7 files | Cohesion: 81%

## When to Use

- Working with code in `src/`
- Understanding how make_progress_hook, hook, print_result work
- Modifying jre_vidget-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/jre_vidget/ui.py` | _progress_task_by_id, make_progress_hook, hook, print_result, print_config (+15) |
| `src/jre_vidget/engine.py` | _ydl_format_for_config, _merge_output_format, _extract_audio_postprocessor, _video_convert_postprocessor, build_ydl_opts (+7) |
| `src/jre_vidget/cli.py` | _resolve, _read_batch_urls, _validate_output, download, batch (+5) |
| `src/jre_vidget/models.py` | load, DownloadConfig, AppConfig, save, VideoFormat (+1) |
| `tests/test_engine.py` | test_build_ydl_opts_mp4, test_build_ydl_opts_mp3_uses_extract_audio, test_build_ydl_opts_progress_hook_attached, test_build_ydl_opts_non_mp4_video_has_convertor, test_download_returns_failed_on_error (+1) |
| `tests/test_models.py` | test_app_config_roundtrip, test_video_format_audio_only |
| `src/jre_vidget/checks.py` | check_dependencies |

## Entry Points

Start here when exploring this area:

- **`make_progress_hook`** (Function) — `src/jre_vidget/ui.py:165`
- **`hook`** (Function) — `src/jre_vidget/ui.py:184`
- **`print_result`** (Function) — `src/jre_vidget/ui.py:235`
- **`print_config`** (Function) — `src/jre_vidget/ui.py:287`
- **`print_error`** (Function) — `src/jre_vidget/ui.py:300`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `DownloadConfig` | Class | `src/jre_vidget/models.py` | 120 |
| `AppConfig` | Class | `src/jre_vidget/models.py` | 137 |
| `VideoFormat` | Class | `src/jre_vidget/models.py` | 61 |
| `VideoInfo` | Class | `src/jre_vidget/models.py` | 85 |
| `make_progress_hook` | Function | `src/jre_vidget/ui.py` | 165 |
| `hook` | Function | `src/jre_vidget/ui.py` | 184 |
| `print_result` | Function | `src/jre_vidget/ui.py` | 235 |
| `print_config` | Function | `src/jre_vidget/ui.py` | 287 |
| `print_error` | Function | `src/jre_vidget/ui.py` | 300 |
| `print_batch_intro` | Function | `src/jre_vidget/ui.py` | 324 |
| `load` | Function | `src/jre_vidget/models.py` | 149 |
| `download` | Function | `src/jre_vidget/cli.py` | 82 |
| `batch` | Function | `src/jre_vidget/cli.py` | 138 |
| `config_show` | Function | `src/jre_vidget/cli.py` | 191 |
| `test_build_ydl_opts_mp4` | Function | `tests/test_engine.py` | 20 |
| `test_build_ydl_opts_mp3_uses_extract_audio` | Function | `tests/test_engine.py` | 27 |
| `test_build_ydl_opts_progress_hook_attached` | Function | `tests/test_engine.py` | 34 |
| `test_build_ydl_opts_non_mp4_video_has_convertor` | Function | `tests/test_engine.py` | 141 |
| `build_ydl_opts` | Function | `src/jre_vidget/engine.py` | 81 |
| `test_app_config_roundtrip` | Function | `tests/test_models.py` | 22 |

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
| `Download → Print_error` | intra_community | 3 |
| `Formats → EngineError` | cross_community | 3 |
| `Formats → _format_upload_date` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 5 calls |

## How to Explore

1. `gitnexus_context({name: "make_progress_hook"})` — see callers and callees
2. `gitnexus_query({query: "jre_vidget"})` — find related execution flows
3. Read key files listed above for implementation details
|||||||
=======
---
name: jre-vidget
description: "Skill for the Jre_vidget area of jre-vidget. 24 symbols across 4 files."
---

# Jre_vidget

24 symbols | 4 files | Cohesion: 83%

## When to Use

- Working with code in `src/`
- Understanding how test_build_ydl_opts_mp4, test_build_ydl_opts_mp3_uses_extract_audio, test_build_ydl_opts_progress_hook_attached work
- Modifying jre_vidget-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/jre_vidget/engine.py` | _ydl_format_for_config, _merge_output_format, _extract_audio_postprocessor, _video_convert_postprocessor, build_ydl_opts (+6) |
| `src/jre_vidget/models.py` | DownloadConfig, VideoFormat, VideoInfo, AppConfig, load (+1) |
| `tests/test_engine.py` | test_build_ydl_opts_mp4, test_build_ydl_opts_mp3_uses_extract_audio, test_build_ydl_opts_progress_hook_attached, test_build_ydl_opts_non_mp4_video_has_convertor, test_download_returns_failed_on_error |
| `tests/test_models.py` | test_video_format_audio_only, test_app_config_roundtrip |

## Entry Points

Start here when exploring this area:

- **`test_build_ydl_opts_mp4`** (Function) — `tests/test_engine.py:19`
- **`test_build_ydl_opts_mp3_uses_extract_audio`** (Function) — `tests/test_engine.py:26`
- **`test_build_ydl_opts_progress_hook_attached`** (Function) — `tests/test_engine.py:33`
- **`test_build_ydl_opts_non_mp4_video_has_convertor`** (Function) — `tests/test_engine.py:115`
- **`build_ydl_opts`** (Function) — `src/jre_vidget/engine.py:80`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `DownloadConfig` | Class | `src/jre_vidget/models.py` | 120 |
| `VideoFormat` | Class | `src/jre_vidget/models.py` | 61 |
| `VideoInfo` | Class | `src/jre_vidget/models.py` | 85 |
| `AppConfig` | Class | `src/jre_vidget/models.py` | 136 |
| `test_build_ydl_opts_mp4` | Function | `tests/test_engine.py` | 19 |
| `test_build_ydl_opts_mp3_uses_extract_audio` | Function | `tests/test_engine.py` | 26 |
| `test_build_ydl_opts_progress_hook_attached` | Function | `tests/test_engine.py` | 33 |
| `test_build_ydl_opts_non_mp4_video_has_convertor` | Function | `tests/test_engine.py` | 115 |
| `build_ydl_opts` | Function | `src/jre_vidget/engine.py` | 80 |
| `test_video_format_audio_only` | Function | `tests/test_models.py` | 17 |
| `test_app_config_roundtrip` | Function | `tests/test_models.py` | 22 |
| `load` | Function | `src/jre_vidget/models.py` | 148 |
| `save` | Function | `src/jre_vidget/models.py` | 153 |
| `test_download_returns_failed_on_error` | Function | `tests/test_engine.py` | 63 |
| `download` | Function | `src/jre_vidget/engine.py` | 257 |
| `_ydl_format_for_config` | Function | `src/jre_vidget/engine.py` | 52 |
| `_merge_output_format` | Function | `src/jre_vidget/engine.py` | 58 |
| `_extract_audio_postprocessor` | Function | `src/jre_vidget/engine.py` | 66 |
| `_video_convert_postprocessor` | Function | `src/jre_vidget/engine.py` | 73 |
| `_format_resolution` | Function | `src/jre_vidget/engine.py` | 126 |

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
| Tests | 2 calls |

## How to Explore

1. `gitnexus_context({name: "test_build_ydl_opts_mp4"})` — see callers and callees
2. `gitnexus_query({query: "jre_vidget"})` — find related execution flows
3. Read key files listed above for implementation details
>>>>>>> Current commit: Add GitNexus docs, Typer CLI, and Rich UI
