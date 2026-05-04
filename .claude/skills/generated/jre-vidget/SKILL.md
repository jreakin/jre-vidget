---
name: jre-vidget
description: "Skill for the Jre_vidget area of jre-vidget. 71 symbols across 12 files."
---

# Jre_vidget

71 symbols | 12 files | Cohesion: 71%

## When to Use

- Working with code in `src/`
- Understanding how test_build_ydl_opts_mp4, test_build_ydl_opts_mp3_uses_extract_audio, test_build_ydl_opts_progress_hook_attached work
- Modifying jre_vidget-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/jre_vidget/ui.py` | print_config, _progress_task_by_id, hook, print_result, print_error (+16) |
| `src/jre_vidget/cli.py` | config_show, auth_status, auth_logout, _resolve, _validate_output (+12) |
| `src/jre_vidget/engine.py` | _ydl_format_for_config, _merge_output_format, _extract_audio_postprocessor, _video_convert_postprocessor, build_ydl_opts (+8) |
| `tests/test_engine.py` | test_build_ydl_opts_mp4, test_build_ydl_opts_mp3_uses_extract_audio, test_build_ydl_opts_progress_hook_attached, test_build_ydl_opts_non_mp4_video_has_convertor, test_download_retries_then_succeeds |
| `src/jre_vidget/models.py` | DownloadConfig, VideoFormat, VideoInfo, load |
| `tests/unit/test_properties_models.py` | _video_info_with_duration, test_video_info_duration_str_unknown_when_none, test_video_format_display_size |
| `tests/unit/test_properties_engine.py` | _minimal_config, test_build_ydl_opts_keys_and_audio_branch |
| `tests/unit/test_auth.py` | test_clears_all_auth_fields, test_saves_to_disk |
| `tests/test_models.py` | test_video_format_audio_only |
| `tests/integration/test_youtube_cli.py` | test_login_saves_credentials |

## Entry Points

Start here when exploring this area:

- **`test_build_ydl_opts_mp4`** (Function) — `tests/test_engine.py:20`
- **`test_build_ydl_opts_mp3_uses_extract_audio`** (Function) — `tests/test_engine.py:27`
- **`test_build_ydl_opts_progress_hook_attached`** (Function) — `tests/test_engine.py:34`
- **`test_build_ydl_opts_non_mp4_video_has_convertor`** (Function) — `tests/test_engine.py:141`
- **`test_build_ydl_opts_keys_and_audio_branch`** (Function) — `tests/unit/test_properties_engine.py:35`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `DownloadConfig` | Class | `src/jre_vidget/models.py` | 149 |
| `VideoFormat` | Class | `src/jre_vidget/models.py` | 62 |
| `VideoInfo` | Class | `src/jre_vidget/models.py` | 114 |
| `test_build_ydl_opts_mp4` | Function | `tests/test_engine.py` | 20 |
| `test_build_ydl_opts_mp3_uses_extract_audio` | Function | `tests/test_engine.py` | 27 |
| `test_build_ydl_opts_progress_hook_attached` | Function | `tests/test_engine.py` | 34 |
| `test_build_ydl_opts_non_mp4_video_has_convertor` | Function | `tests/test_engine.py` | 141 |
| `test_build_ydl_opts_keys_and_audio_branch` | Function | `tests/unit/test_properties_engine.py` | 35 |
| `build_ydl_opts` | Function | `src/jre_vidget/engine.py` | 84 |
| `test_video_format_audio_only` | Function | `tests/test_models.py` | 17 |
| `test_video_info_duration_str_unknown_when_none` | Function | `tests/unit/test_properties_models.py` | 150 |
| `test_video_format_display_size` | Function | `tests/unit/test_properties_models.py` | 163 |
| `test_clears_all_auth_fields` | Function | `tests/unit/test_auth.py` | 173 |
| `test_saves_to_disk` | Function | `tests/unit/test_auth.py` | 191 |
| `test_login_saves_credentials` | Function | `tests/integration/test_youtube_cli.py` | 50 |
| `print_config` | Function | `src/jre_vidget/ui.py` | 315 |
| `load` | Function | `src/jre_vidget/models.py` | 212 |
| `config_show` | Function | `src/jre_vidget/cli.py` | 332 |
| `auth_status` | Function | `src/jre_vidget/cli.py` | 411 |
| `auth_logout` | Function | `src/jre_vidget/cli.py` | 423 |

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
| Unit | 8 calls |
| Tests | 6 calls |
| Integration | 4 calls |

## How to Explore

1. `gitnexus_context({name: "test_build_ydl_opts_mp4"})` — see callers and callees
2. `gitnexus_query({query: "jre_vidget"})` — find related execution flows
3. Read key files listed above for implementation details
