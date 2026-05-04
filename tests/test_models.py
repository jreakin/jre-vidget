"""Unit tests for Pydantic models (phase 2)."""

from jre_vidget.config import load_app_config, save_app_config
from jre_vidget.models import (
    AppConfig,
    BatchJob,
    DownloadConfig,
    DownloadResult,
    DownloadStatus,
    Quality,
    VideoFormat,
)


def test_quality_ydl_format() -> None:
    assert "720" in Quality.P720.ydl_format


def test_video_format_audio_only() -> None:
    f = VideoFormat(format_id="a1", ext="m4a", vcodec="none")
    assert f.is_audio_only


def test_app_config_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("jre_vidget.config.CONFIG_PATH", tmp_path / "config.json")
    cfg = AppConfig(quality=Quality.P720)
    save_app_config(cfg)
    loaded = load_app_config()
    assert loaded.quality == Quality.P720


def test_batch_job_counts() -> None:
    cfg = DownloadConfig(url="https://example.com")
    job = BatchJob(urls=["a", "b", "c"], config=cfg)
    job.results.append(DownloadResult(url="a", status=DownloadStatus.SUCCESS))
    job.results.append(DownloadResult(url="b", status=DownloadStatus.FAILED))
    assert job.completed == 1
    assert job.failed == 1
