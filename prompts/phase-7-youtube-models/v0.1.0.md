# Phase 7 — YouTube Publish: Models
# Version: 0.1.0
# Model: claude-sonnet-4-6
# Last Updated: 2026-05-03
# Maintainer: jreakin
# Status: Draft

---

## Goal

Extend `models.py` with the three new Pydantic v2 models required for YouTube publish
support, and embed `AuthConfig` into the existing `AppConfig` so credentials persist
alongside user preferences.

---

## Spec Reference

`docs/superpowers/specs/2026-05-03-youtube-publish-design.md` — Models section.

---

## Files

| Action | File |
|--------|------|
| Modify | `src/jre_vidget/models.py` |
| Create | `tests/unit/test_youtube_models.py` |

---

## Context

`models.py` already contains: `Quality`, `OutputFormat`, `VideoFormat`, `VideoInfo`,
`DownloadConfig`, `AppConfig`, `DownloadStatus`, `DownloadResult`, `BatchJob`.

`AppConfig` is stored at `~/.vidget/config.json` via `jre_vidget.config.save_app_config` /
`load_app_config` (plaintext OAuth fields where set; see `config.py`).

---

## Implementation

### Step 1 — Write failing tests first

Create `tests/unit/test_youtube_models.py`:

```python
"""Tests for YouTube publish models."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest
from pydantic import ValidationError

from jre_vidget.config import load_app_config, save_app_config
from jre_vidget.models import AppConfig, AuthConfig, PublishConfig, PublishResult


class TestAuthConfig:
    def test_defaults(self):
        cfg = AuthConfig()
        assert cfg.client_id is None
        assert cfg.client_secret is None
        assert cfg.refresh_token is None

    def test_round_trips_json(self):
        cfg = AuthConfig(
            client_id="cid",
            client_secret="csecret",
            refresh_token="rtoken",
        )
        restored = AuthConfig.model_validate_json(cfg.model_dump_json())
        assert restored.client_id == "cid"
        assert restored.refresh_token == "rtoken"

    def test_partial_population(self):
        cfg = AuthConfig(client_id="only-id")
        assert cfg.client_secret is None
        assert cfg.refresh_token is None


class TestPublishConfig:
    def test_required_fields(self, tmp_path):
        filepath = tmp_path / "video.mp4"
        filepath.touch()
        cfg = PublishConfig(filepath=filepath, title="My Video")
        assert cfg.title == "My Video"
        assert cfg.privacy == "public"
        assert cfg.remove_after_upload is False
        assert cfg.description == ""

    def test_title_is_required(self, tmp_path):
        with pytest.raises(ValidationError):
            PublishConfig(filepath=tmp_path / "video.mp4")  # missing title

    def test_privacy_options(self, tmp_path):
        filepath = tmp_path / "video.mp4"
        filepath.touch()
        for privacy in ("public", "unlisted", "private"):
            cfg = PublishConfig(filepath=filepath, title="t", privacy=privacy)
            assert cfg.privacy == privacy

    def test_invalid_privacy_rejected(self, tmp_path):
        with pytest.raises(ValidationError):
            PublishConfig(
                filepath=tmp_path / "video.mp4",
                title="t",
                privacy="secret",  # type: ignore[arg-type]
            )

    def test_remove_after_upload_flag(self, tmp_path):
        cfg = PublishConfig(
            filepath=tmp_path / "video.mp4",
            title="t",
            remove_after_upload=True,
        )
        assert cfg.remove_after_upload is True


class TestPublishResult:
    def test_url_construction(self):
        result = PublishResult(
            video_id="abc123",
            url="https://youtube.com/watch?v=abc123",
            title="My Video",
            privacy="public",
        )
        assert "abc123" in result.url
        assert result.removed_local_file is False

    def test_removed_local_file_flag(self):
        result = PublishResult(
            video_id="x",
            url="https://youtube.com/watch?v=x",
            title="t",
            privacy="public",
            removed_local_file=True,
        )
        assert result.removed_local_file is True


class TestAppConfigEmbedding:
    def test_app_config_has_auth(self):
        cfg = AppConfig()
        assert hasattr(cfg, "auth")
        assert isinstance(cfg.auth, AuthConfig)
        assert cfg.auth.refresh_token is None

    def test_app_config_persists_auth(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token="mytoken")
        save_app_config(cfg)

        restored = load_app_config()
        assert restored.auth.refresh_token == "mytoken"
```

Run — confirm ALL fail:
```bash
uv run pytest tests/unit/test_youtube_models.py -v
```
Expected: `ImportError` or `AttributeError` (models don't exist yet).

---

### Step 2 — Add models to `models.py`

Insert the following block **immediately before the `AppConfig` class** (not after
`BatchJob` — `AppConfig` must see `AuthConfig` at definition time). Do **not** remove
or modify any existing models.

```python
# ---------------------------------------------------------------------------
# YouTube publish models
# ---------------------------------------------------------------------------

class AuthConfig(BaseModel):
    """YouTube OAuth credentials — persisted inside AppConfig."""

    client_id: str | None = None
    client_secret: str | None = None
    refresh_token: str | None = None


class PublishConfig(BaseModel):
    """Options for a single YouTube upload job."""

    filepath: Path
    title: str                                          # required — no default
    description: str = ""
    privacy: Literal["public", "unlisted", "private"] = "public"
    remove_after_upload: bool = False


class PublishResult(BaseModel):
    """Outcome of a completed YouTube upload."""

    video_id: str
    url: str                                            # https://youtube.com/watch?v=...
    title: str
    privacy: str
    removed_local_file: bool = False
```

Also add `Literal` to the `typing` import at the top of `models.py` if not already present:
```python
from typing import Any, Literal
```

---

### Step 3 — Embed `AuthConfig` in `AppConfig`

Add the `auth` field to `AppConfig`:

```python
class AppConfig(BaseModel):
    """User preferences persisted under ~/.vidget/config.json."""

    output_dir: Path = Field(default_factory=lambda: Path.home() / "Downloads")
    quality: Quality = Quality.BEST
    format: OutputFormat = OutputFormat.MP4
    subtitles: bool = False
    max_concurrent: int = 3
    auth: AuthConfig = Field(default_factory=AuthConfig)   # ← add this line

    model_config = {"arbitrary_types_allowed": True}
    # ... rest of AppConfig unchanged
```

The new models block is already placed before `AppConfig` (Step 2), so `AuthConfig`
is in scope when `AppConfig` references it.

---

### Step 4 — Run tests

```bash
uv run pytest tests/unit/test_youtube_models.py -v
```
Expected: all tests **PASS**.

Also confirm no existing tests broke:
```bash
uv run pytest tests/unit/ -v
```

---

### Step 5 — Type check and lint

```bash
uv run mypy src/jre_vidget/models.py --strict
uv run ruff check src/jre_vidget/models.py
```
Expected: no errors.

---

### Step 6 — Commit

```bash
git add src/jre_vidget/models.py tests/unit/test_youtube_models.py
git commit -m "feat: add AuthConfig, PublishConfig, PublishResult models"
```

---

## Acceptance Criteria

- [ ] `AuthConfig`, `PublishConfig`, `PublishResult` importable from `jre_vidget.models`
- [ ] `AppConfig` has an `auth: AuthConfig` field that round-trips through JSON
- [ ] All new models validate correctly with Pydantic v2
- [ ] All tests in `test_youtube_models.py` pass
- [ ] No existing tests broken
- [ ] `mypy --strict` clean on `models.py`
