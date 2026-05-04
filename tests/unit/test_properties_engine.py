"""Property-based tests for deterministic engine helpers (Hypothesis)."""

from __future__ import annotations

from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from jre_vidget.engine import build_ydl_opts
from jre_vidget.models import DownloadConfig, OutputFormat, Quality


def _minimal_config(
    *,
    quality: Quality,
    fmt: OutputFormat,
    subtitles: bool,
) -> DownloadConfig:
    return DownloadConfig(
        url="https://example.com/watch?v=x",
        quality=quality,
        format=fmt,
        output_dir=Path("/tmp/vidget-hypothesis-out"),
        subtitles=subtitles,
        retries=2,
    )


@settings(max_examples=120, deadline=None)
@given(
    st.sampled_from(list(Quality)),
    st.sampled_from(list(OutputFormat)),
    st.booleans(),
)
def test_build_ydl_opts_keys_and_audio_branch(
    quality: Quality,
    fmt: OutputFormat,
    subtitles: bool,
) -> None:
    cfg = _minimal_config(quality=quality, fmt=fmt, subtitles=subtitles)
    opts = build_ydl_opts(cfg)

    assert "format" in opts
    assert opts["outtmpl"] == cfg.output_template
    assert opts["noplaylist"] is True
    assert "quiet" in opts

    if fmt.is_audio_only:
        assert "merge_output_format" not in opts
        pps = opts.get("postprocessors", [])
        assert any(p.get("key") == "FFmpegExtractAudio" for p in pps)
        assert any(p.get("preferredcodec") == fmt.value for p in pps)
    else:
        assert "merge_output_format" in opts
        merge = opts["merge_output_format"]
        assert merge in ("mp4", "mkv", "mov")
        pps = opts.get("postprocessors") or []
        if fmt is not OutputFormat.MP4:
            assert any(p.get("key") == "FFmpegVideoConvertor" for p in pps)
        else:
            assert not any(p.get("key") == "FFmpegVideoConvertor" for p in pps)

    if subtitles:
        assert opts.get("writesubtitles") is True
        assert opts.get("writeautomaticsub") is True
    else:
        assert opts.get("writesubtitles") is not True
        assert opts.get("writeautomaticsub") is not True
