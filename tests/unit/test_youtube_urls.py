"""Tests for canonical YouTube watch URL construction."""

from __future__ import annotations

from jre_vidget.youtube_urls import build_youtube_watch_url


def test_build_youtube_watch_url_strips_nothing_but_formats() -> None:
    assert build_youtube_watch_url("abc123_XYZ") == "https://youtube.com/watch?v=abc123_XYZ"
