---
name: integration
description: "Skill for the Integration area of jre-vidget. 17 symbols across 4 files."
---

# Integration

17 symbols | 4 files | Cohesion: 73%

## When to Use

- Working with code in `tests/`
- Understanding how test_app_config_roundtrip, test_url_construction, test_removed_local_file_flag work
- Modifying integration-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/integration/test_youtube_cli.py` | test_shows_connected_when_token_present, test_logout_clears_token, test_publish_success, test_publish_with_custom_title, test_publish_exits_1_on_publish_error (+4) |
| `tests/unit/test_youtube_models.py` | test_url_construction, test_removed_local_file_flag, test_app_config_has_auth, test_app_config_persists_auth |
| `src/jre_vidget/models.py` | PublishResult, AppConfig, save |
| `tests/test_models.py` | test_app_config_roundtrip |

## Entry Points

Start here when exploring this area:

- **`test_app_config_roundtrip`** (Function) — `tests/test_models.py:22`
- **`test_url_construction`** (Function) — `tests/unit/test_youtube_models.py:76`
- **`test_removed_local_file_flag`** (Function) — `tests/unit/test_youtube_models.py:86`
- **`test_app_config_has_auth`** (Function) — `tests/unit/test_youtube_models.py:98`
- **`test_app_config_persists_auth`** (Function) — `tests/unit/test_youtube_models.py:104`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `PublishResult` | Class | `src/jre_vidget/models.py` | 189 |
| `AppConfig` | Class | `src/jre_vidget/models.py` | 199 |
| `test_app_config_roundtrip` | Function | `tests/test_models.py` | 22 |
| `test_url_construction` | Function | `tests/unit/test_youtube_models.py` | 76 |
| `test_removed_local_file_flag` | Function | `tests/unit/test_youtube_models.py` | 86 |
| `test_app_config_has_auth` | Function | `tests/unit/test_youtube_models.py` | 98 |
| `test_app_config_persists_auth` | Function | `tests/unit/test_youtube_models.py` | 104 |
| `test_shows_connected_when_token_present` | Function | `tests/integration/test_youtube_cli.py` | 75 |
| `test_logout_clears_token` | Function | `tests/integration/test_youtube_cli.py` | 106 |
| `test_publish_success` | Function | `tests/integration/test_youtube_cli.py` | 126 |
| `test_publish_with_custom_title` | Function | `tests/integration/test_youtube_cli.py` | 150 |
| `test_publish_exits_1_on_publish_error` | Function | `tests/integration/test_youtube_cli.py` | 193 |
| `test_publish_privacy_flag` | Function | `tests/integration/test_youtube_cli.py` | 214 |
| `test_download_publish_calls_fetch_info_first` | Function | `tests/integration/test_youtube_cli.py` | 243 |
| `test_download_publish_uses_scraped_title` | Function | `tests/integration/test_youtube_cli.py` | 293 |
| `test_download_publish_title_override` | Function | `tests/integration/test_youtube_cli.py` | 342 |
| `save` | Function | `src/jre_vidget/models.py` | 217 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Auth_logout → Save` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Unit | 11 calls |
| Jre_vidget | 3 calls |
| Tests | 3 calls |

## How to Explore

1. `gitnexus_context({name: "test_app_config_roundtrip"})` — see callers and callees
2. `gitnexus_query({query: "integration"})` — find related execution flows
3. Read key files listed above for implementation details
