"""Property-based tests for pure model invariants (Hypothesis)."""

from __future__ import annotations

import re
from datetime import datetime

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite
from pydantic import SecretStr

from jre_vidget.models import (
    AuthConfig,
    BatchJob,
    DownloadConfig,
    DownloadResult,
    DownloadStatus,
    OutputFormat,
    Quality,
    VideoFormat,
    VideoInfo,
    VideoPreview,
)

_AUDIO_FORMATS = frozenset(
    {
        OutputFormat.MP3,
        OutputFormat.M4A,
        OutputFormat.AAC,
        OutputFormat.WAV,
        OutputFormat.FLAC,
    }
)


def _parse_duration_display(display: str) -> int:
    parts = display.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    msg = f"unexpected duration display: {display!r}"
    raise ValueError(msg)


@composite
def _video_preview(draw: st.DrawFn) -> VideoPreview:
    duration_seconds = draw(st.integers(min_value=0, max_value=10_000_000))
    return VideoPreview(
        url="https://example.com/watch?v=x",
        title="t",
        description="d",
        duration_seconds=duration_seconds,
        thumbnail_url="https://i.ytimg.com/vi/x.jpg",
        uploader="u",
        channel_url=None,
        view_count=None,
        upload_date=None,
        formats=[],
    )


@composite
def _video_info_with_duration(draw: st.DrawFn) -> VideoInfo:
    duration = draw(st.integers(min_value=0, max_value=10_000_000))
    return VideoInfo(
        id="id",
        title="title",
        url="https://example.com",
        webpage_url="https://example.com",
        duration=duration,
        thumbnail=None,
        uploader=None,
        upload_date=None,
        formats=[],
        subtitles={},
    )


@composite
def _auth_config(draw: st.DrawFn) -> AuthConfig:
    text = st.text(max_size=64)
    cs = draw(st.one_of(st.none(), text))
    rt = draw(st.one_of(st.none(), text))
    return AuthConfig(
        client_id=draw(st.one_of(st.none(), text)),
        client_secret=SecretStr(cs) if cs is not None else None,
        refresh_token=SecretStr(rt) if rt is not None else None,
    )


@composite
def _download_results(draw: st.DrawFn) -> list[DownloadResult]:
    n = draw(st.integers(min_value=0, max_value=40))
    statuses = draw(
        st.lists(
            st.sampled_from(list(DownloadStatus)),
            min_size=n,
            max_size=n,
        )
    )
    return [
        DownloadResult(
            url=f"https://example.com/{i}",
            status=st,
            filepath=None,
            error=None if st == DownloadStatus.SUCCESS else "err",
            duration_s=None,
            finished_at=datetime.min.replace(tzinfo=None),
        )
        for i, st in enumerate(statuses)
    ]


@settings(max_examples=40, deadline=None)
@given(st.sampled_from(list(Quality)))
def test_quality_ydl_format_nonempty(quality: Quality) -> None:
    yf = quality.ydl_format
    assert len(yf) > 0
    if quality is Quality.AUDIO:
        assert "bestaudio" in yf


@settings(max_examples=20, deadline=None)
@given(st.sampled_from(list(OutputFormat)))
def test_output_format_audio_only_matches_set(fmt: OutputFormat) -> None:
    assert fmt.is_audio_only == (fmt in _AUDIO_FORMATS)


@settings(max_examples=60, deadline=None)
@given(_video_preview())
def test_video_preview_duration_display_roundtrip(preview: VideoPreview) -> None:
    display = preview.duration_display
    if preview.duration_seconds < 3600:
        assert re.fullmatch(r"\d{1,4}:\d{2}", display), display
    else:
        assert re.fullmatch(r"\d+:\d{2}:\d{2}", display), display
    assert _parse_duration_display(display) == preview.duration_seconds


@settings(max_examples=60, deadline=None)
@given(_video_info_with_duration())
def test_video_info_duration_str_roundtrip(info: VideoInfo) -> None:
    assert info.duration is not None
    display = info.duration_str
    if info.duration < 3600:
        assert re.fullmatch(r"\d{1,4}:\d{2}", display), display
    else:
        assert re.fullmatch(r"\d+:\d{2}:\d{2}", display), display
    assert _parse_duration_display(display) == info.duration


def test_video_info_duration_str_unknown_when_none() -> None:
    info = VideoInfo(
        id="i",
        title="t",
        url="u",
        webpage_url="w",
        duration=None,
    )
    assert info.duration_str == "unknown"


@settings(max_examples=80, deadline=None)
@given(st.one_of(st.none(), st.integers(min_value=0, max_value=2**50)))
def test_video_format_display_size(filesize: int | None) -> None:
    vf = VideoFormat(
        format_id="1",
        ext="mp4",
        vcodec="h264",
        filesize=filesize,
    )
    text = vf.display_size
    if filesize is None:
        assert text == "unknown"
    else:
        assert text.endswith(" MB")
        num = float(text.removesuffix(" MB"))
        assert num >= 0
        expected_mb = filesize / 1_048_576
        assert abs(num - round(expected_mb, 1)) < 0.05 or abs(num - expected_mb) < 0.1


@settings(max_examples=50, deadline=None)
@given(_auth_config())
def test_auth_config_python_dump_roundtrip(cfg: AuthConfig) -> None:
    """``model_dump_json`` masks SecretStr; in-memory dump preserves secrets."""
    restored = AuthConfig.model_validate(cfg.model_dump(mode="python"))
    assert restored == cfg


@settings(max_examples=50, deadline=None)
@given(_download_results())
def test_batch_job_counts_consistent(results: list[DownloadResult]) -> None:
    cfg = DownloadConfig(url="https://example.com")
    job = BatchJob(urls=["x"], config=cfg, results=results)
    success = sum(1 for r in results if r.status == DownloadStatus.SUCCESS)
    failed = sum(1 for r in results if r.status == DownloadStatus.FAILED)
    assert job.completed == success
    assert job.failed == failed
    assert job.completed + job.failed <= len(results)
