"""Unit tests for jre_vidget.engine (mocked yt-dlp, no network)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from yt_dlp.utils import DownloadError

from jre_vidget.engine import EngineError, build_ydl_opts, download, download_batch, fetch_info
from jre_vidget.models import (
    BatchJob,
    DownloadConfig,
    DownloadStatus,
    OutputFormat,
    Quality,
)


def test_build_ydl_opts_mp4() -> None:
    cfg = DownloadConfig(url="https://x.com", quality=Quality.P720, format=OutputFormat.MP4)
    opts = build_ydl_opts(cfg)
    assert "720" in opts["format"]
    assert opts["merge_output_format"] == "mp4"


def test_build_ydl_opts_mp3_uses_extract_audio() -> None:
    cfg = DownloadConfig(url="https://x.com", format=OutputFormat.MP3)
    opts = build_ydl_opts(cfg)
    pp = opts["postprocessors"]
    assert any(p["key"] == "FFmpegExtractAudio" for p in pp)


def test_build_ydl_opts_progress_hook_attached() -> None:
    def hook(_d: object) -> None:
        return None

    cfg = DownloadConfig(url="https://x.com")
    opts = build_ydl_opts(cfg, progress_hook=hook)
    assert hook in opts["progress_hooks"]


def test_fetch_info_maps_fields() -> None:
    fake_info = {
        "id": "abc123",
        "title": "Test Video",
        "webpage_url": "https://x.com",
        "duration": 305,
        "thumbnail": None,
        "uploader": None,
        "upload_date": None,
        "formats": [],
        "subtitles": {},
    }
    with patch("yt_dlp.YoutubeDL") as MockYDL:
        instance = MagicMock()
        instance.extract_info.return_value = fake_info
        MockYDL.return_value.__enter__.return_value = instance
        info = fetch_info("https://x.com")
    assert info.id == "abc123"
    assert info.duration_str == "5:05"


def test_download_returns_failed_on_error() -> None:
    cfg = DownloadConfig(url="https://x.com")
    with patch("yt_dlp.YoutubeDL") as MockYDL:
        instance = MagicMock()
        instance.download.side_effect = DownloadError("404")
        MockYDL.return_value.__enter__.return_value = instance
        result = download(cfg)
    assert result.status == DownloadStatus.FAILED
    assert result.error is not None
    assert "404" in result.error


def test_download_batch_never_raises_on_engine_error() -> None:
    job = BatchJob(
        urls=["https://a.com", "https://b.com"],
        config=DownloadConfig(url="https://placeholder.com"),
    )

    def boom(_cfg: object, _hook: object | None = None) -> object:
        raise EngineError("boom")

    with patch("jre_vidget.engine.download", side_effect=boom):
        out = download_batch(job)
    assert len(out.results) == 2
    assert all(r.status == DownloadStatus.FAILED for r in out.results)
    assert all(r.error == "boom" for r in out.results)


def test_download_batch_calls_on_result() -> None:
    job = BatchJob(urls=["https://a.com"], config=DownloadConfig(url="https://a.com"))
    seen: list[str] = []

    def fake_download(cfg: DownloadConfig, _hook: object | None = None) -> object:
        from jre_vidget.models import DownloadResult

        return DownloadResult(url=cfg.url, status=DownloadStatus.SUCCESS)

    def on_result(r: object) -> None:
        from jre_vidget.models import DownloadResult

        assert isinstance(r, DownloadResult)
        seen.append(r.url)

    with patch("jre_vidget.engine.download", side_effect=fake_download):
        download_batch(job, on_result=on_result)
    assert seen == ["https://a.com"]


@pytest.mark.parametrize(
    "fmt",
    [OutputFormat.MKV, OutputFormat.MOV],
)
def test_build_ydl_opts_non_mp4_video_has_convertor(fmt: OutputFormat) -> None:
    cfg = DownloadConfig(url="https://x.com", format=fmt)
    opts = build_ydl_opts(cfg)
    pp = opts.get("postprocessors") or []
    assert any(p["key"] == "FFmpegVideoConvertor" for p in pp)
    assert opts.get("merge_output_format") == fmt.value
