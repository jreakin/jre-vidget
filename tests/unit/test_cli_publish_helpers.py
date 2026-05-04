"""Unit tests for ``PublishOptions`` and publish-title helpers in ``cli``."""

from __future__ import annotations

from pathlib import Path

from jre_vidget.cli import (
    PublishOptions,
    _publish_config_for_downloaded_file,
    _resolve_publish_title_for_download,
)
from jre_vidget.models import PrivacyStatus, VideoInfo


def test_resolve_publish_title_explicit_wins() -> None:
    info = VideoInfo(
        id="1",
        title="scraped",
        url="https://u",
        webpage_url="https://u",
    )
    opts = PublishOptions(
        title="CLI title",
        description="d",
        privacy=PrivacyStatus.UNLISTED,
        remove_after_upload=False,
    )
    assert (
        _resolve_publish_title_for_download(opts, video_info=info, fallback_url="https://u")
        == "CLI title"
    )


def test_resolve_publish_title_empty_string_falls_back_to_scraped() -> None:
    info = VideoInfo(
        id="1",
        title="scraped",
        url="https://u",
        webpage_url="https://u",
    )
    opts = PublishOptions(
        title="",
        description="",
        privacy=PrivacyStatus.PUBLIC,
        remove_after_upload=False,
    )
    assert (
        _resolve_publish_title_for_download(opts, video_info=info, fallback_url="https://u")
        == "scraped"
    )


def test_resolve_publish_title_none_uses_video_info() -> None:
    info = VideoInfo(
        id="1",
        title="from info",
        url="https://u",
        webpage_url="https://u",
    )
    opts = PublishOptions(
        title=None,
        description="",
        privacy=PrivacyStatus.PRIVATE,
        remove_after_upload=True,
    )
    assert (
        _resolve_publish_title_for_download(opts, video_info=info, fallback_url="https://fallback")
        == "from info"
    )


def test_resolve_publish_title_fallback_url_when_no_info() -> None:
    opts = PublishOptions(
        title=None,
        description="",
        privacy=PrivacyStatus.PUBLIC,
        remove_after_upload=False,
    )
    assert (
        _resolve_publish_title_for_download(opts, video_info=None, fallback_url="https://only-url")
        == "https://only-url"
    )


def test_publish_config_for_downloaded_file_matches_options(tmp_path: Path) -> None:
    fp = tmp_path / "out.mp4"
    fp.touch()
    info = VideoInfo(
        id="1",
        title="ignored when cli title set",
        url="https://u",
        webpage_url="https://u",
    )
    opts = PublishOptions(
        title="Final title",
        description="body text",
        privacy=PrivacyStatus.UNLISTED,
        remove_after_upload=True,
    )
    cfg = _publish_config_for_downloaded_file(
        fp,
        opts,
        video_info=info,
        url="https://u",
    )
    assert cfg.filepath == fp
    assert cfg.title == "Final title"
    assert cfg.description == "body text"
    assert cfg.privacy == PrivacyStatus.UNLISTED
    assert cfg.remove_after_upload is True
