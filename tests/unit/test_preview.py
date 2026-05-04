"""Unit tests for metadata preview (engine.preview)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import yt_dlp

from jre_vidget.engine import preview
from jre_vidget.models import DownloadError, VideoPreview

FAKE_INFO = {
    "title": "JRE #1234 — Guest Name",
    "description": "Episode description here.",
    "duration": 7320,
    "thumbnail": "https://i.ytimg.com/vi/abc123/maxresdefault.jpg",
    "uploader": "PowerfulJRE",
    "channel_url": "https://www.youtube.com/@PowerfulJRE",
    "view_count": 1_500_000,
    "upload_date": "20260101",
    "formats": [
        {"format_note": "1080p60"},
        {"format_note": "720p"},
        {"format_note": "480p"},
        {"format_note": "1080p60"},  # duplicate — should be deduplicated
    ],
}


def _make_mock_ydl(info: dict | None = None, raises: BaseException | None = None) -> MagicMock:
    mock_ydl = MagicMock()
    if raises is not None:
        mock_ydl.__enter__.return_value.extract_info.side_effect = raises
    else:
        mock_ydl.__enter__.return_value.extract_info.return_value = info
    mock_ydl.__exit__.return_value = False
    return mock_ydl


def test_preview_returns_video_preview() -> None:
    with patch("yt_dlp.YoutubeDL", return_value=_make_mock_ydl(FAKE_INFO)):
        result = preview("https://youtube.com/watch?v=abc123")

    assert isinstance(result, VideoPreview)
    assert result.title == "JRE #1234 — Guest Name"
    assert result.duration_seconds == 7320
    assert result.uploader == "PowerfulJRE"


def test_preview_duration_display_hours() -> None:
    with patch("yt_dlp.YoutubeDL", return_value=_make_mock_ydl(FAKE_INFO)):
        result = preview("https://youtube.com/watch?v=abc123")
    assert result.duration_display == "2:02:00"


def test_preview_deduplicates_formats() -> None:
    with patch("yt_dlp.YoutubeDL", return_value=_make_mock_ydl(FAKE_INFO)):
        result = preview("https://youtube.com/watch?v=abc123")
    assert result.formats.count("1080p60") == 1
    assert "720p" in result.formats
    assert "480p" in result.formats


def test_preview_raises_on_download_error() -> None:
    with (
        patch(
            "yt_dlp.YoutubeDL",
            return_value=_make_mock_ydl(raises=yt_dlp.utils.DownloadError("not found")),
        ),
        pytest.raises(DownloadError),
    ):
        preview("https://bad.url/video")


def test_preview_raises_when_info_is_none() -> None:
    with (
        patch("yt_dlp.YoutubeDL", return_value=_make_mock_ydl(info=None)),
        pytest.raises(DownloadError, match="No metadata returned"),
    ):
        preview("https://youtube.com/watch?v=abc123")


def test_preview_handles_missing_optional_fields() -> None:
    minimal_info = {
        "title": "Short Video",
        "description": "",
        "duration": 45,
        "thumbnail": "",
        "uploader": "SomeChannel",
        "formats": [],
    }
    with patch("yt_dlp.YoutubeDL", return_value=_make_mock_ydl(minimal_info)):
        result = preview("https://youtube.com/watch?v=xyz")
    assert result.duration_display == "0:45"
    assert result.view_count is None
    assert result.channel_url is None
    assert result.formats == []
