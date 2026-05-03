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
