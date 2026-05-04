"""CLI tests (Typer CliRunner, mocked engine)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from jre_vidget.cli import app
from jre_vidget.models import BatchJob, DownloadResult, DownloadStatus, VideoInfo

runner = CliRunner()
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(s: str) -> str:
    return _ANSI_ESCAPE.sub("", s)


def test_download_help() -> None:
    result = runner.invoke(app, ["download", "--help"], color=False)
    assert result.exit_code == 0
    plain = _strip_ansi(result.output)
    assert "--quality" in plain


def test_batch_missing_file_exits_1() -> None:
    result = runner.invoke(app, ["batch", "/nonexistent/urls.txt"])
    assert result.exit_code == 1


def test_config_show_runs() -> None:
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0


def test_download_success(tmp_path: Path) -> None:
    fake_result = DownloadResult(
        url="https://x.com",
        status=DownloadStatus.SUCCESS,
        filepath=tmp_path / "video.mp4",
    )
    with patch("jre_vidget.cli.engine.download", return_value=fake_result):
        result = runner.invoke(
            app,
            ["download", "https://x.com", "--output", str(tmp_path)],
        )
    assert result.exit_code == 0


def test_download_failure_exits_1(tmp_path: Path) -> None:
    fake_result = DownloadResult(
        url="https://x.com",
        status=DownloadStatus.FAILED,
        error="404",
    )
    with patch("jre_vidget.cli.engine.download", return_value=fake_result):
        result = runner.invoke(app, ["download", "https://x.com"])
    assert result.exit_code == 1


def test_download_json_stdout(tmp_path: Path) -> None:
    fake_result = DownloadResult(
        url="https://x.com",
        status=DownloadStatus.SUCCESS,
        filepath=tmp_path / "video.mp4",
    )
    with patch("jre_vidget.cli.engine.download", return_value=fake_result):
        result = runner.invoke(
            app,
            ["download", "https://x.com", "--output", str(tmp_path), "--json"],
        )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["download"]["status"] == "success"
    assert "publish" not in data


def test_formats_json_stdout() -> None:
    info = VideoInfo(
        id="abc",
        title="Hello",
        url="https://x.com",
        webpage_url="https://x.com",
    )
    with patch("jre_vidget.cli.engine.fetch_info", return_value=info):
        result = runner.invoke(app, ["formats", "https://x.com", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["id"] == "abc"
    assert data["title"] == "Hello"


def test_batch_json_stdout(tmp_path: Path) -> None:
    urls_file = tmp_path / "urls.txt"
    urls_file.write_text("https://a.com\n", encoding="utf-8")

    def fake_batch(job: BatchJob, **_kwargs: object) -> BatchJob:
        job.results.append(
            DownloadResult(url="https://a.com", status=DownloadStatus.SUCCESS),
        )
        return job

    with patch("jre_vidget.cli.engine.download_batch", side_effect=fake_batch):
        result = runner.invoke(
            app,
            ["batch", str(urls_file), "--output", str(tmp_path), "--json"],
        )
    assert result.exit_code == 0
    rows = json.loads(result.stdout)
    assert len(rows) == 1
    assert rows[0]["url"] == "https://a.com"
