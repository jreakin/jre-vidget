"""
YouTube Data API v3 upload wrapper for jre-vidget.

Pure upload logic — no CLI, no Rich, no auth management.
Mirrors engine.py in structure.

Public API:
  upload(config, auth, progress_hook=None) -> PublishResult
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httplib2
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from jre_vidget import auth
from jre_vidget.models import AuthConfig, PublishConfig, PublishResult
from jre_vidget.youtube_urls import build_youtube_watch_url

UploadProgressHook = Callable[[int, int], None]  # (bytes_uploaded, total_bytes)


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

    http = AuthorizedHttp(creds, http=httplib2.Http())
    youtube = build("youtube", "v3", http=http, cache_discovery=False)

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
        response: dict[str, Any] | None = None
        while response is None:
            status, chunk = request.next_chunk()
            if status is not None and progress_hook is not None:
                progress_hook(status.resumable_progress, status.total_size)
            if isinstance(chunk, dict):
                response = chunk
            elif chunk is not None:
                raise PublishError(
                    f"Unexpected upload response: expected dict or None, got {type(chunk).__name__}"
                )
    except HttpError as e:
        raise PublishError(str(e)) from e

    video_id = str(response["id"])
    result = PublishResult(
        video_id=video_id,
        url=build_youtube_watch_url(video_id),
        title=config.title,
        privacy=config.privacy,
    )

    if config.remove_after_upload:
        config.filepath.unlink()
        result = result.model_copy(update={"removed_local_file": True})

    return result
