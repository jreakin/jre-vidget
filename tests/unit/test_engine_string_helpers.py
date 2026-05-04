"""Unit tests for engine raw-dict string helpers and title coercion in ``_raw_to_video_info``."""

from __future__ import annotations

from unittest.mock import patch

from jre_vidget.engine import _optional_str_field, _raw_to_video_info, _str_field, preview


def test_str_field_missing_and_types() -> None:
    assert _str_field({}, "k") == ""
    assert _str_field({"k": "x"}, "k") == "x"
    assert _str_field({"k": 1}, "k") == ""
    assert _str_field({"k": ""}, "k") == ""


def test_optional_str_field() -> None:
    assert _optional_str_field({}, "k") is None
    assert _optional_str_field({"k": "x"}, "k") == "x"
    assert _optional_str_field({"k": ""}, "k") == ""
    assert _optional_str_field({"k": 1}, "k") is None


def test_raw_to_video_info_webpage_url_fallback() -> None:
    raw: dict = {"id": "a", "title": "t", "formats": [], "subtitles": {}}
    info = _raw_to_video_info(raw, "https://fallback.example/watch?v=1")
    assert info.webpage_url == "https://fallback.example/watch?v=1"
    assert info.url == info.webpage_url


def test_raw_to_video_info_webpage_url_when_str_present() -> None:
    raw: dict = {
        "id": "a",
        "title": "t",
        "webpage_url": "https://site.example/v/1",
        "formats": [],
        "subtitles": {},
    }
    info = _raw_to_video_info(raw, "https://fallback.example/")
    assert info.webpage_url == "https://site.example/v/1"


def test_raw_to_video_info_title_coerces_non_str() -> None:
    """Non-string ``title`` from yt-dlp should stringify like the pre-refactor path."""
    raw: dict = {"id": "1", "title": 42, "formats": [], "subtitles": {}}
    info = _raw_to_video_info(raw, "https://x")
    assert info.title == "42"


def test_preview_coerces_title_uploader_description() -> None:
    """``preview`` should stringify scalars the same way as ``fetch_info`` / ``_raw_to_video_info``."""
    fake_raw: dict = {
        "id": "z",
        "title": 100,
        "description": 200,
        "uploader": 300,
        "duration": 1,
        "formats": [],
        "subtitles": {},
    }

    with patch("jre_vidget.engine._extract_raw_info", return_value=fake_raw):
        meta = preview("https://example.com/watch")

    assert meta.title == "100"
    assert meta.description == "200"
    assert meta.uploader == "300"
