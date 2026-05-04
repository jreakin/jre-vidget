"""Integration-style CLI tests (mocked engine, no network)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from jre_vidget.cli import app
from jre_vidget.models import BatchJob, DownloadResult, DownloadStatus

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "vidget" in result.output


def test_keyboard_interrupt_handled(tmp_path: Path) -> None:
    with patch("jre_vidget.cli.engine.download", side_effect=KeyboardInterrupt):
        result = runner.invoke(
            app,
            ["download", "https://x.com", "--output", str(tmp_path)],
        )
    assert result.exit_code == 130


def test_config_reset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("jre_vidget.models.CONFIG_PATH", tmp_path / "config.json")
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text('{"output_dir": "/tmp"}', encoding="utf-8")
    result = runner.invoke(app, ["config", "reset", "--yes"])
    assert result.exit_code == 0
    assert not cfg_path.exists()


def test_output_dir_created(tmp_path: Path) -> None:
    new_dir = tmp_path / "new_subdir"
    fake_result = DownloadResult(
        url="https://x.com",
        status=DownloadStatus.SUCCESS,
        filepath=new_dir / "video.mp4",
    )
    with patch("jre_vidget.cli.engine.download", return_value=fake_result):
        result = runner.invoke(
            app,
            ["download", "https://x.com", "--output", str(new_dir)],
        )
    assert new_dir.exists()
    assert result.exit_code == 0


def test_batch_with_comments(tmp_path: Path) -> None:
    urls_file = tmp_path / "urls.txt"
    urls_file.write_text("# comment\nhttps://x.com\n\nhttps://y.com\n")
    captured: list[BatchJob] = []

    def fake_batch(job: BatchJob, **_kwargs: object) -> BatchJob:
        captured.append(job)
        for url in job.urls:
            job.results.append(DownloadResult(url=url, status=DownloadStatus.SUCCESS))
        return job

    with patch("jre_vidget.cli.engine.download_batch", side_effect=fake_batch):
        result = runner.invoke(
            app,
            ["batch", str(urls_file), "--output", str(tmp_path)],
        )
    assert result.exit_code == 0
    assert captured[0].urls == ["https://x.com", "https://y.com"]
