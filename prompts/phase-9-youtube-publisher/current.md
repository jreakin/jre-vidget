# Phase 9 — YouTube Publish: Publisher Module
# Version: 0.1.0
# Model: claude-sonnet-4-6
# Last Updated: 2026-05-03
# Maintainer: jreakin
# Status: Draft

---

## Goal

Implement `publisher.py` — the YouTube Data API v3 upload wrapper. Accepts a
`PublishConfig` and `AuthConfig`, uploads the file with resumable chunked transfer,
calls an optional progress hook, and returns a `PublishResult`. No CLI, no Rich.

---

## Spec Reference

`docs/superpowers/specs/2026-05-03-youtube-publish-design.md` — `publisher.py` section.

---

## Prerequisites

- Phase 7 complete (`PublishConfig`, `PublishResult` importable)
- Phase 8 complete (`auth.get_credentials` importable)
- Google API dependencies installed (`google-api-python-client`, `google-auth-httplib2`)

---

## Files

| Action | File |
|--------|------|
| Create | `src/jre_vidget/publisher.py` |
| Create | `tests/unit/test_publisher.py` |

---

## Implementation

### Step 1 — Write failing tests

Create `tests/unit/test_publisher.py`:

```python
"""Tests for publisher.py — mocked YouTube API, no real uploads."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from jre_vidget.auth import AuthError
from jre_vidget.models import AuthConfig, PublishConfig, PublishResult
from jre_vidget.publisher import PublishError, upload


@pytest.fixture()
def video_file(tmp_path: Path) -> Path:
    f = tmp_path / "video.mp4"
    f.write_bytes(b"fake video content")
    return f


@pytest.fixture()
def auth_config() -> AuthConfig:
    return AuthConfig(
        client_id="cid",
        client_secret="csecret",
        refresh_token="rt",
    )


@pytest.fixture()
def publish_config(video_file: Path) -> PublishConfig:
    return PublishConfig(
        filepath=video_file,
        title="Test Video",
        description="A test description",
        privacy="public",
    )


class TestUploadSuccess:
    def test_returns_publish_result(self, publish_config, auth_config):
        mock_creds = MagicMock()
        mock_youtube = MagicMock()
        mock_insert = MagicMock()
        mock_insert.next_chunk.side_effect = [(None, {"id": "abc123"})]
        mock_youtube.videos.return_value.insert.return_value = mock_insert

        with patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds):
            with patch("jre_vidget.publisher.build", return_value=mock_youtube):
                with patch("jre_vidget.publisher.MediaFileUpload"):
                    result = upload(publish_config, auth_config)

        assert isinstance(result, PublishResult)
        assert result.video_id == "abc123"
        assert result.url == "https://youtube.com/watch?v=abc123"
        assert result.title == "Test Video"
        assert result.privacy == "public"
        assert result.removed_local_file is False

    def test_insert_called_with_correct_metadata(self, publish_config, auth_config):
        mock_creds = MagicMock()
        mock_youtube = MagicMock()
        mock_insert = MagicMock()
        mock_insert.next_chunk.side_effect = [(None, {"id": "vid1"})]
        mock_youtube.videos.return_value.insert.return_value = mock_insert

        with patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds):
            with patch("jre_vidget.publisher.build", return_value=mock_youtube):
                with patch("jre_vidget.publisher.MediaFileUpload"):
                    upload(publish_config, auth_config)

        insert_call = mock_youtube.videos.return_value.insert.call_args
        body = insert_call[1]["body"]
        assert body["snippet"]["title"] == "Test Video"
        assert body["snippet"]["description"] == "A test description"
        assert body["status"]["privacyStatus"] == "public"

    def test_media_file_upload_resumable(self, publish_config, auth_config, video_file):
        mock_creds = MagicMock()
        mock_youtube = MagicMock()
        mock_youtube.videos.return_value.insert.return_value.next_chunk.side_effect = [
            (None, {"id": "x"})
        ]

        with patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds):
            with patch("jre_vidget.publisher.build", return_value=mock_youtube):
                with patch("jre_vidget.publisher.MediaFileUpload") as mock_media:
                    upload(publish_config, auth_config)

        mock_media.assert_called_once_with(str(video_file), resumable=True)


class TestUploadWithProgressHook:
    def test_progress_hook_called(self, publish_config, auth_config):
        mock_creds = MagicMock()
        mock_youtube = MagicMock()
        # Simulate two chunks then completion
        mock_request = MagicMock()
        mock_request.next_chunk.side_effect = [
            (MagicMock(total_size=100, resumable_progress=50), None),
            (None, {"id": "done123"}),
        ]
        mock_youtube.videos.return_value.insert.return_value = mock_request

        progress_calls: list[tuple[int, int]] = []

        def hook(uploaded: int, total: int) -> None:
            progress_calls.append((uploaded, total))

        with patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds):
            with patch("jre_vidget.publisher.build", return_value=mock_youtube):
                with patch("jre_vidget.publisher.MediaFileUpload"):
                    result = upload(publish_config, auth_config, progress_hook=hook)

        assert result.video_id == "done123"
        assert len(progress_calls) >= 1


class TestUploadRemoveAfterUpload:
    def test_removes_file_on_success(self, tmp_path, auth_config):
        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")
        config = PublishConfig(
            filepath=video,
            title="t",
            remove_after_upload=True,
        )

        mock_creds = MagicMock()
        mock_youtube = MagicMock()
        mock_youtube.videos.return_value.insert.return_value.next_chunk.side_effect = [
            (None, {"id": "r1"})
        ]

        with patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds):
            with patch("jre_vidget.publisher.build", return_value=mock_youtube):
                with patch("jre_vidget.publisher.MediaFileUpload"):
                    result = upload(config, auth_config)

        assert not video.exists()
        assert result.removed_local_file is True

    def test_does_not_remove_file_on_failure(self, tmp_path, auth_config):
        from googleapiclient.errors import HttpError

        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")
        config = PublishConfig(
            filepath=video,
            title="t",
            remove_after_upload=True,
        )

        mock_http_error = HttpError(
            resp=MagicMock(status=403),
            content=b'{"error": {"message": "quota exceeded"}}',
        )
        mock_creds = MagicMock()
        mock_youtube = MagicMock()
        mock_youtube.videos.return_value.insert.return_value.next_chunk.side_effect = (
            mock_http_error
        )

        with patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds):
            with patch("jre_vidget.publisher.build", return_value=mock_youtube):
                with patch("jre_vidget.publisher.MediaFileUpload"):
                    with pytest.raises(PublishError):
                        upload(config, auth_config)

        assert video.exists()  # file NOT deleted on failure


class TestUploadErrors:
    def test_raises_auth_error_when_not_configured(self, publish_config):
        auth = AuthConfig()  # no credentials

        with patch(
            "jre_vidget.publisher.auth.get_credentials",
            side_effect=AuthError("Run 'vidget auth login'"),
        ):
            with pytest.raises(AuthError):
                upload(publish_config, auth)

    def test_raises_publish_error_on_http_error(self, publish_config, auth_config):
        from googleapiclient.errors import HttpError

        mock_creds = MagicMock()
        mock_http_error = HttpError(
            resp=MagicMock(status=400),
            content=b'{"error": {"message": "invalid title"}}',
        )
        mock_youtube = MagicMock()
        mock_youtube.videos.return_value.insert.return_value.next_chunk.side_effect = (
            mock_http_error
        )

        with patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds):
            with patch("jre_vidget.publisher.build", return_value=mock_youtube):
                with patch("jre_vidget.publisher.MediaFileUpload"):
                    with pytest.raises(PublishError):
                        upload(publish_config, auth_config)

    def test_raises_publish_error_on_missing_file(self, auth_config, tmp_path):
        config = PublishConfig(
            filepath=tmp_path / "nonexistent.mp4",
            title="t",
        )
        with pytest.raises(PublishError, match="File not found"):
            upload(config, auth_config)
```

Run — confirm all fail:
```bash
uv run pytest tests/unit/test_publisher.py -v
```
Expected: `ModuleNotFoundError: No module named 'jre_vidget.publisher'`

---

### Step 2 — Implement `publisher.py`

Create `src/jre_vidget/publisher.py`:

```python
"""
YouTube Data API v3 upload wrapper for jre-vidget.

Pure upload logic — no CLI, no Rich, no auth management.
Mirrors engine.py in structure.

Public API:
  upload(config, auth, progress_hook=None) -> PublishResult
"""

from __future__ import annotations

from collections.abc import Callable

import googleapiclient.discovery
import httplib2
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from jre_vidget import auth
from jre_vidget.models import AuthConfig, PublishConfig, PublishResult

UploadProgressHook = Callable[[int, int], None]  # (bytes_uploaded, total_bytes)

# Use the same alias as the rest of the codebase expects
build = googleapiclient.discovery.build


class PublishError(Exception):
    """Raised when the YouTube API rejects the upload or returns an error."""


def upload(
    config: PublishConfig,
    auth_config: AuthConfig,
    progress_hook: UploadProgressHook | None = None,
) -> PublishResult:
    """
    Upload a local video file to YouTube.

    Steps:
    1. Verify the file exists
    2. Get valid credentials via auth.get_credentials()
    3. Build MediaFileUpload with resumable=True
    4. Call youtube.videos().insert() with metadata from config
    5. Drive next_chunk() loop, calling progress_hook after each chunk
    6. On success → return PublishResult
    7. If remove_after_upload → delete local file ONLY after video_id confirmed
    8. On HttpError → raise PublishError with API message

    Raises:
        PublishError: file not found, API rejection, or unexpected error
        AuthError: re-raised from auth.get_credentials() if not authenticated
    """
    if not config.filepath.exists():
        raise PublishError(f"File not found: {config.filepath}")

    creds = auth.get_credentials(auth_config)  # raises AuthError if not configured

    youtube = build("youtube", "v3", credentials=creds)

    media = MediaFileUpload(str(config.filepath), resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": config.title,
                "description": config.description,
            },
            "status": {
                "privacyStatus": config.privacy,
            },
        },
        media_body=media,
    )

    try:
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status is not None and progress_hook is not None:
                progress_hook(status.resumable_progress, status.total_size)
    except HttpError as e:
        raise PublishError(str(e)) from e

    video_id: str = response["id"]
    result = PublishResult(
        video_id=video_id,
        url=f"https://youtube.com/watch?v={video_id}",
        title=config.title,
        privacy=config.privacy,
    )

    if config.remove_after_upload:
        config.filepath.unlink()
        result = result.model_copy(update={"removed_local_file": True})

    return result
```

---

### Step 3 — Run tests

```bash
uv run pytest tests/unit/test_publisher.py -v
```
Expected: all tests **PASS**.

Confirm no regressions:
```bash
uv run pytest tests/unit/ -v
```

---

### Step 4 — Type check and lint

```bash
uv run mypy src/jre_vidget/publisher.py --strict
uv run ruff check src/jre_vidget/publisher.py
```
Expected: no errors.

---

### Step 5 — Commit

```bash
git add src/jre_vidget/publisher.py tests/unit/test_publisher.py
git commit -m "feat: add YouTube publisher module with resumable upload"
```

---

## Acceptance Criteria

- [ ] `publisher.py` exports `PublishError`, `UploadProgressHook`, `upload`
- [ ] `upload()` uses `MediaFileUpload(resumable=True)`
- [ ] `upload()` calls `progress_hook` after each chunk when provided
- [ ] `upload()` deletes local file after confirmed upload when `remove_after_upload=True`
- [ ] `upload()` never deletes local file when upload fails
- [ ] `upload()` raises `PublishError` for missing file, HTTP errors
- [ ] `auth.AuthError` propagates unchanged (not wrapped in `PublishError`)
- [ ] All tests in `test_publisher.py` pass
- [ ] No existing tests broken
- [ ] `mypy --strict` clean
