"""Unit tests for jre_vidget.engine (mocked yt-dlp, no network)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from yt_dlp.utils import DownloadError

from jre_vidget.engine import (
    YDL_SOCKET_TIMEOUT_SECONDS,
    EngineError,
    _attempt_download_once,
    build_ydl_opts,
    download,
    download_batch,
    fetch_info,
)
from jre_vidget.models import (
    BatchJob,
    DownloadConfig,
    DownloadResult,
    DownloadStatus,
    OutputFormat,
    Quality,
)


def test_build_ydl_opts_mp4() -> None:
    cfg = DownloadConfig(url="https://x.com", quality=Quality.P720, format=OutputFormat.MP4)
    opts = build_ydl_opts(cfg)
    assert "720" in opts["format"]
    assert opts["merge_output_format"] == "mp4"
    assert opts["socket_timeout"] == YDL_SOCKET_TIMEOUT_SECONDS


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


def test_download_sets_filepath_from_finished_hook(tmp_path: Path) -> None:
    out_file = tmp_path / "vid.mp4"
    out_file.write_bytes(b"x")
    cfg = DownloadConfig(url="https://x.com", output_dir=tmp_path)

    with patch("yt_dlp.YoutubeDL") as MockYDL:
        instance = MagicMock()

        def download_side_effect(_urls: list[str]) -> None:
            call_opts = MockYDL.call_args[0][0]
            hooks = call_opts.get("progress_hooks") or []
            for h in hooks:
                h({"status": "finished", "filename": str(out_file)})

        instance.download.side_effect = download_side_effect
        MockYDL.return_value.__enter__.return_value = instance
        result = download(cfg)

    assert result.status == DownloadStatus.SUCCESS
    assert result.filepath == out_file


def test_download_batch_preserves_url_order_with_thread_pool() -> None:
    urls = ["https://a.com", "https://b.com", "https://c.com"]
    job = BatchJob(
        urls=urls,
        config=DownloadConfig(url="", max_concurrent=2),
    )

    def track(cfg: DownloadConfig, _hook: object | None = None) -> DownloadResult:
        return DownloadResult(url=cfg.url, status=DownloadStatus.SUCCESS)

    with patch("jre_vidget.engine.download", side_effect=track):
        out = download_batch(job)
    assert [r.url for r in out.results] == urls


def test_download_maps_non_ytdlp_exception_to_engine_error(tmp_path: Path) -> None:
    cfg = DownloadConfig(url="https://x.com", output_dir=tmp_path)
    with (
        patch("jre_vidget.engine._attempt_download_once", side_effect=RuntimeError("disk full")),
        pytest.raises(EngineError, match="disk full"),
    ):
        download(cfg)


def test_attempt_download_once_invokes_youtube_dl() -> None:
    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = instance
        _attempt_download_once("https://example.com/watch?v=1", {"quiet": True})
    instance.download.assert_called_once_with(["https://example.com/watch?v=1"])


def test_download_retries_then_succeeds(tmp_path: Path) -> None:
    cfg = DownloadConfig(url="https://x.com", output_dir=tmp_path, retries=2)
    call_count = 0

    def download_side_effect(_urls: list[str]) -> None:
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise DownloadError("transient")
        return None

    with (
        patch("yt_dlp.YoutubeDL") as MockYDL,
        patch("jre_vidget.engine.time.sleep") as mock_sleep,
    ):
        instance = MagicMock()
        instance.download.side_effect = download_side_effect
        MockYDL.return_value.__enter__.return_value = instance
        result = download(cfg)

    assert result.status == DownloadStatus.SUCCESS
    assert call_count == 3
    assert mock_sleep.call_count == 2


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
