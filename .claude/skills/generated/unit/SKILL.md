---
name: unit
description: "Skill for the Unit area of jre-vidget. 53 symbols across 11 files."
---

# Unit

53 symbols | 11 files | Cohesion: 77%

## When to Use

- Working with code in `tests/`
- Understanding how test_defaults, test_round_trips_json, test_partial_population work
- Modifying unit-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/unit/test_publisher.py` | auth_config, test_raises_auth_error_when_not_configured, publish_config, test_removes_file_on_success, test_does_not_remove_file_on_failure (+6) |
| `tests/unit/test_auth.py` | test_returns_credentials_when_configured, test_raises_auth_error_when_no_refresh_token, test_raises_auth_error_when_no_credentials_at_all, test_refreshes_expired_token, test_raises_auth_error_on_refresh_failure (+6) |
| `tests/unit/test_preview.py` | _make_mock_ydl, test_preview_returns_video_preview, test_preview_duration_display_hours, test_preview_deduplicates_formats, test_preview_raises_on_download_error (+2) |
| `tests/unit/test_youtube_models.py` | test_defaults, test_round_trips_json, test_partial_population, test_required_fields, test_privacy_options (+1) |
| `tests/unit/test_properties_models.py` | _auth_config, _video_preview, _parse_duration_display, test_video_preview_duration_display_roundtrip, test_video_info_duration_str_roundtrip |
| `src/jre_vidget/models.py` | AuthConfig, VideoPreview, PublishConfig |
| `src/jre_vidget/auth.py` | AuthError, get_credentials, login_browser |
| `tests/integration/test_youtube_cli.py` | test_login_prompts_for_credentials, test_publish_exits_3_when_not_authenticated |
| `src/jre_vidget/engine.py` | _thumbnail_url_from_info, preview |
| `src/jre_vidget/publisher.py` | PublishError, upload |

## Entry Points

Start here when exploring this area:

- **`test_defaults`** (Function) — `tests/unit/test_youtube_models.py:13`
- **`test_round_trips_json`** (Function) — `tests/unit/test_youtube_models.py:19`
- **`test_partial_population`** (Function) — `tests/unit/test_youtube_models.py:29`
- **`auth_config`** (Function) — `tests/unit/test_publisher.py:22`
- **`test_raises_auth_error_when_not_configured`** (Function) — `tests/unit/test_publisher.py:194`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `AuthConfig` | Class | `src/jre_vidget/models.py` | 171 |
| `AuthError` | Class | `src/jre_vidget/auth.py` | 26 |
| `VideoPreview` | Class | `src/jre_vidget/models.py` | 90 |
| `PublishConfig` | Class | `src/jre_vidget/models.py` | 179 |
| `PublishError` | Class | `src/jre_vidget/publisher.py` | 27 |
| `test_defaults` | Function | `tests/unit/test_youtube_models.py` | 13 |
| `test_round_trips_json` | Function | `tests/unit/test_youtube_models.py` | 19 |
| `test_partial_population` | Function | `tests/unit/test_youtube_models.py` | 29 |
| `auth_config` | Function | `tests/unit/test_publisher.py` | 22 |
| `test_raises_auth_error_when_not_configured` | Function | `tests/unit/test_publisher.py` | 194 |
| `test_returns_credentials_when_configured` | Function | `tests/unit/test_auth.py` | 59 |
| `test_raises_auth_error_when_no_refresh_token` | Function | `tests/unit/test_auth.py` | 74 |
| `test_raises_auth_error_when_no_credentials_at_all` | Function | `tests/unit/test_auth.py` | 79 |
| `test_refreshes_expired_token` | Function | `tests/unit/test_auth.py` | 84 |
| `test_raises_auth_error_on_refresh_failure` | Function | `tests/unit/test_auth.py` | 100 |
| `test_env_vars_override_config` | Function | `tests/unit/test_auth.py` | 117 |
| `test_env_var_refresh_token_overrides_config` | Function | `tests/unit/test_auth.py` | 135 |
| `test_env_var_refresh_token_allows_empty_config` | Function | `tests/unit/test_auth.py` | 153 |
| `test_login_prompts_for_credentials` | Function | `tests/integration/test_youtube_cli.py` | 28 |
| `test_publish_exits_3_when_not_authenticated` | Function | `tests/integration/test_youtube_cli.py` | 176 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Auth_login → AuthConfig` | cross_community | 3 |
| `Auth_logout → AuthConfig` | cross_community | 3 |
| `Preview → _format_resolution` | cross_community | 3 |
| `Upload → AuthError` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 2 calls |
| Integration | 2 calls |
| Jre_vidget | 2 calls |

## How to Explore

1. `gitnexus_context({name: "test_defaults"})` — see callers and callees
2. `gitnexus_query({query: "unit"})` — find related execution flows
3. Read key files listed above for implementation details
