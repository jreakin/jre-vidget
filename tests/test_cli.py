"""CLI tests (Typer CliRunner, mocked engine)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import SecretStr
from typer.testing import CliRunner

from jre_vidget import auth
from jre_vidget import config as vidget_config
from jre_vidget import history as history_mod
from jre_vidget.cli import app, resolve_download_config
from jre_vidget.config import load_app_config, save_app_config
from jre_vidget.models import (
    AppConfig,
    AuthConfig,
    BatchJob,
    DownloadResult,
    DownloadStatus,
    OutputFormat,
    Quality,
    VideoInfo,
)

runner = CliRunner()
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(s: str) -> str:
    return _ANSI_ESCAPE.sub("", s)


def test_download_help() -> None:
    result = runner.invoke(app, ["download", "--help"], color=False)
    assert result.exit_code == 0
    plain = _strip_ansi(result.output)
    assert "--quality" in plain
    assert "--subs" in plain


def test_cli_reexports_share_dependency_modules_with_cli_common() -> None:
    """Legacy ``patch("jre_vidget.cli.engine", ...)`` targets the same modules as ``cli_common``."""
    import jre_vidget.cli as cli_mod
    import jre_vidget.cli_common as common

    assert cli_mod.engine is common.engine
    assert cli_mod.auth is common.auth
    assert cli_mod.publisher is common.publisher
    assert cli_mod.checks is common.checks
    assert cli_mod.ui is common.ui


def test_legacy_cli_patch_path_still_mocks_engine() -> None:
    """Phase prompts and external tests often patch ``jre_vidget.cli.engine``."""
    from jre_vidget.models import VideoPreview

    fake = VideoPreview(
        url="https://youtube.com/watch?v=legacy",
        title="Legacy patch",
        description="",
        duration_seconds=1,
        thumbnail_url="https://example.com/t.jpg",
        uploader="u",
    )
    with patch("jre_vidget.cli.engine.preview", return_value=fake):
        result = runner.invoke(app, ["preview", "--json", "https://youtube.com/watch?v=legacy"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["title"] == "Legacy patch"


def test_resolve_download_config_subs_tri_state(tmp_path: Path) -> None:
    """None → saved default; False/--no-subs must override cfg.subtitles=True."""
    cfg = AppConfig(output_dir=tmp_path, subtitles=True)
    assert resolve_download_config(cfg, None, None, None, None, "https://x.com").subtitles is True
    assert resolve_download_config(cfg, None, None, None, False, "https://x.com").subtitles is False
    cfg_off = AppConfig(output_dir=tmp_path, subtitles=False)
    assert (
        resolve_download_config(cfg_off, None, None, None, True, "https://x.com").subtitles is True
    )


def test_resolve_download_config_quality_format_output_merge(tmp_path: Path) -> None:
    """None defers to AppConfig; explicit CLI values override quality, format, output_dir."""
    base_out = tmp_path / "from_config"
    base_out.mkdir()
    override_out = tmp_path / "from_cli"
    override_out.mkdir()
    cfg = AppConfig(output_dir=base_out, quality=Quality.BEST, format=OutputFormat.MP4)
    merged = resolve_download_config(cfg, None, None, None, None, "https://x.com")
    assert merged.quality is Quality.BEST
    assert merged.format is OutputFormat.MP4
    assert merged.output_dir == base_out

    overridden = resolve_download_config(
        cfg,
        Quality.P720,
        OutputFormat.MKV,
        override_out,
        None,
        "https://x.com",
    )
    assert overridden.quality is Quality.P720
    assert overridden.format is OutputFormat.MKV
    assert overridden.output_dir == override_out


def test_resolve_download_config_max_concurrent_optional(tmp_path: Path) -> None:
    cfg = AppConfig(output_dir=tmp_path)
    assert resolve_download_config(cfg, None, None, None, None, "https://x.com").max_concurrent == 3
    assert (
        resolve_download_config(cfg, None, None, None, None, "", max_concurrent=7).max_concurrent
        == 7
    )


def test_download_publish_missing_filepath_exits_1(tmp_path: Path) -> None:
    fake_result = DownloadResult(
        url="https://x.com",
        status=DownloadStatus.SUCCESS,
        filepath=None,
    )
    info = VideoInfo(
        id="1",
        title="T",
        url="https://x.com",
        webpage_url="https://x.com",
    )
    with (
        patch("jre_vidget.cli_common.engine.download", return_value=fake_result),
        patch("jre_vidget.cli_common.engine.fetch_info", return_value=info),
    ):
        result = runner.invoke(
            app,
            ["download", "https://x.com", "--output", str(tmp_path), "--publish"],
        )
    assert result.exit_code == 1


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
    with patch("jre_vidget.cli_common.engine.download", return_value=fake_result):
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
    with patch("jre_vidget.cli_common.engine.download", return_value=fake_result):
        result = runner.invoke(app, ["download", "https://x.com"])
    assert result.exit_code == 1


def test_download_json_stdout(tmp_path: Path) -> None:
    fake_result = DownloadResult(
        url="https://x.com",
        status=DownloadStatus.SUCCESS,
        filepath=tmp_path / "video.mp4",
    )
    with patch("jre_vidget.cli_common.engine.download", return_value=fake_result):
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
    with patch("jre_vidget.cli_common.engine.fetch_info", return_value=info):
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

    with patch("jre_vidget.cli_common.engine.download_batch", side_effect=fake_batch):
        result = runner.invoke(
            app,
            ["batch", str(urls_file), "--output", str(tmp_path), "--json"],
        )
    assert result.exit_code == 0
    rows = json.loads(result.stdout)
    assert len(rows) == 1
    assert rows[0]["url"] == "https://a.com"


def test_config_set_quality_persists(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.json"
    monkeypatch.setattr(vidget_config, "CONFIG_PATH", cfg_path)
    result = runner.invoke(app, ["config", "set", "--quality", "720p"])
    assert result.exit_code == 0
    loaded = load_app_config()
    assert loaded.quality == Quality.P720


def test_config_reset_yes_removes_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.json"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(AppConfig().model_dump_json(), encoding="utf-8")
    monkeypatch.setattr(vidget_config, "CONFIG_PATH", cfg_path)
    result = runner.invoke(app, ["config", "reset", "--yes"])
    assert result.exit_code == 0
    assert not cfg_path.exists()


def test_auth_status_connected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.json"
    monkeypatch.setattr(vidget_config, "CONFIG_PATH", cfg_path)
    cfg = AppConfig(
        auth=AuthConfig(refresh_token=SecretStr("not-empty")),
    )
    save_app_config(cfg)
    result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "connected" in combined.lower()


def test_auth_status_not_connected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.json"
    monkeypatch.setattr(vidget_config, "CONFIG_PATH", cfg_path)
    save_app_config(AppConfig())
    result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "not connected" in combined.lower()


def test_auth_logout_invokes_logout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.json"
    monkeypatch.setattr(vidget_config, "CONFIG_PATH", cfg_path)
    save_app_config(
        AppConfig(
            auth=AuthConfig(refresh_token=SecretStr("rt")),
        ),
    )
    with patch("jre_vidget.cli_common.auth.logout", wraps=auth.logout) as wrapped:
        result = runner.invoke(app, ["auth", "logout"])
    assert result.exit_code == 0
    wrapped.assert_called_once()


def test_history_append_cli(tmp_path: Path) -> None:
    hist = tmp_path / "uploads.json"
    hist.write_text('{"uploads": []}', encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "history",
            "append",
            "--file",
            str(hist),
            "--video-id",
            "abc123",
            "--title",
            "T",
            "--source-url",
            "https://youtu.be/x",
            "--privacy",
            "public",
            "--run-id",
            "99",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(hist.read_text(encoding="utf-8"))
    assert data["schemaVersion"] == history_mod.UPLOADS_SCHEMA_VERSION
    assert data["uploads"][0]["video_id"] == "abc123"


def test_history_append_invalid_privacy_exit_2(tmp_path: Path) -> None:
    hist = tmp_path / "uploads.json"
    hist.write_text('{"uploads": []}', encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "history",
            "append",
            "--file",
            str(hist),
            "--video-id",
            "abc",
            "--source-url",
            "https://youtu.be/x",
            "--privacy",
            "super-secret",
            "--run-id",
            "1",
        ],
    )
    assert result.exit_code == 2
    combined = (result.stdout or "") + (result.stderr or "")
    assert "privacy must be public, unlisted, or private" in combined


def test_download_invalid_privacy_exit_2(tmp_path: Path) -> None:
    with patch("jre_vidget.cli_common.checks.check_dependencies"):
        result = runner.invoke(
            app,
            [
                "download",
                "https://x.com",
                "--output",
                str(tmp_path),
                "--privacy",
                "invalid",
            ],
        )
    assert result.exit_code == 2
    combined = (result.stdout or "") + (result.stderr or "")
    plain = _strip_ansi(combined)
    assert "Invalid value" in plain and "privacy" in plain.lower()
    assert "public" in plain and "unlisted" in plain and "private" in plain


def test_publish_invalid_privacy_exit_2(tmp_path: Path) -> None:
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"x")
    with patch("jre_vidget.cli_common.checks.check_dependencies"):
        result = runner.invoke(
            app,
            ["publish", str(video), "--privacy", "not-a-privacy"],
        )
    assert result.exit_code == 2
    combined = (result.stdout or "") + (result.stderr or "")
    plain = _strip_ansi(combined)
    assert "Invalid value" in plain and "privacy" in plain.lower()
    assert "public" in plain and "unlisted" in plain and "private" in plain


def test_history_append_corrupt_json_exits_1(tmp_path: Path) -> None:
    hist = tmp_path / "uploads.json"
    hist.write_text("{not valid json", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "history",
            "append",
            "--file",
            str(hist),
            "--video-id",
            "x",
            "--source-url",
            "https://u",
            "--privacy",
            "public",
            "--run-id",
            "1",
        ],
    )
    assert result.exit_code == 1


def test_history_append_env_only(tmp_path: Path) -> None:
    hist = tmp_path / "uploads.json"
    hist.write_text('{"uploads": []}', encoding="utf-8")
    result = runner.invoke(
        app,
        ["history", "append", "--file", str(hist)],
        env={
            "VIDEO_ID": "envvid",
            "INPUT_TITLE": "",
            "INPUT_URL": "https://source",
            "INPUT_PRIVACY": "unlisted",
            "RUN_ID": "4242",
        },
    )
    assert result.exit_code == 0
    data = json.loads(hist.read_text(encoding="utf-8"))
    assert data["uploads"][0]["video_id"] == "envvid"
    assert data["uploads"][0]["privacy"] == "unlisted"
    assert data["uploads"][0]["title"] == "untitled"


def test_history_append_json_stdout(tmp_path: Path) -> None:
    hist = tmp_path / "uploads.json"
    hist.write_text('{"uploads": []}', encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "history",
            "append",
            "--file",
            str(hist),
            "--video-id",
            "j1",
            "--title",
            "JT",
            "--source-url",
            "https://j",
            "--privacy",
            "private",
            "--run-id",
            "7",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["record"]["video_id"] == "j1"
    assert payload["record"]["privacy"] == "private"


def test_history_append_json_error_stdout(tmp_path: Path) -> None:
    hist = tmp_path / "uploads.json"
    hist.write_text(json.dumps({"uploads": {}}), encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "history",
            "append",
            "--file",
            str(hist),
            "--json",
            "--video-id",
            "x",
            "--source-url",
            "https://u",
            "--privacy",
            "public",
            "--run-id",
            "1",
        ],
    )
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "uploads" in payload["error"].lower()
