"""Unit tests for ``progress_hook_session`` and ``commands.download`` helpers."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from jre_vidget import cli_common
from jre_vidget.cli_common import progress_hook_session
from jre_vidget.commands import download as download_cmd
from jre_vidget.engine import EngineError
from jre_vidget.models import (
    DownloadConfig,
    DownloadResult,
    DownloadStatus,
    OutputFormat,
    PrivacyStatus,
    PublishResult,
    Quality,
    VideoInfo,
)


def test_progress_hook_session_json_skips_rich_ui() -> None:
    with (
        patch("jre_vidget.cli_common.ui.make_progress_hook") as mock_mph,
        progress_hook_session(json_output=True) as hook,
    ):
        assert hook is None
    mock_mph.assert_not_called()


def test_progress_hook_session_interactive_enters_progress_context() -> None:
    sentinel_hook = object()
    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = None
    mock_ctx.__exit__.return_value = None
    with (
        patch(
            "jre_vidget.cli_common.ui.make_progress_hook",
            return_value=(sentinel_hook, mock_ctx),
        ),
        progress_hook_session(json_output=False) as hook,
    ):
        assert hook is sentinel_hook
    mock_ctx.__enter__.assert_called_once()
    mock_ctx.__exit__.assert_called_once()


def test_load_video_info_for_publish_success() -> None:
    info = VideoInfo(id="x", title="t", url="https://u", webpage_url="https://u")
    with patch.object(cli_common.engine, "fetch_info", return_value=info):
        out = download_cmd.load_video_info_for_publish("https://u", json_output=True)
    assert out is info


def test_load_video_info_for_publish_engine_error_json_warns_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with patch.object(
        cli_common.engine,
        "fetch_info",
        side_effect=EngineError("boom"),
    ):
        out = download_cmd.load_video_info_for_publish("https://u", json_output=True)
    assert out is None
    err = capsys.readouterr().err
    assert "warning" in err.lower()
    assert "video info" in err.lower()


def test_load_video_info_for_publish_engine_error_rich_warns_console() -> None:
    printed: list[str] = []

    def capture_print(*args: object, **kwargs: object) -> None:
        printed.append(str(args[0]) if args else "")

    with (
        patch.object(
            cli_common.engine,
            "fetch_info",
            side_effect=EngineError("boom"),
        ),
        patch.object(download_cmd.cc.console, "print", side_effect=capture_print),
    ):
        out = download_cmd.load_video_info_for_publish("https://u", json_output=False)
    assert out is None
    assert any("Warning" in p for p in printed)


def test_run_engine_download_json_uses_none_hook() -> None:
    cfg = DownloadConfig(url="https://x", quality=Quality.BEST, format=OutputFormat.MP4)
    result = DownloadResult(url=cfg.url, status=DownloadStatus.SUCCESS)
    with patch.object(download_cmd.cc.engine, "download", return_value=result) as mock_dl:
        out = download_cmd.run_engine_download(cfg, json_output=True)
    assert out is result
    mock_dl.assert_called_once_with(cfg, progress_hook=None)


def test_run_engine_download_rich_passes_session_hook() -> None:
    sent = object()
    cfg = DownloadConfig(url="https://x", quality=Quality.BEST, format=OutputFormat.MP4)
    result = DownloadResult(url=cfg.url, status=DownloadStatus.SUCCESS)

    @contextmanager
    def fake_session(*, json_output: bool) -> Iterator[Any]:
        assert json_output is False
        yield sent

    with (
        patch.object(download_cmd.cc, "progress_hook_session", fake_session),
        patch.object(download_cmd.cc.engine, "download", return_value=result) as mock_dl,
    ):
        out = download_cmd.run_engine_download(cfg, json_output=False)
    assert out is result
    mock_dl.assert_called_once_with(cfg, progress_hook=sent)


def test_emit_download_json_stdout_download_only() -> None:
    dl = DownloadResult(
        url="https://u",
        status=DownloadStatus.FAILED,
        error="e",
        finished_at=datetime(2020, 1, 1),
    )
    echoed: list[str] = []
    with patch.object(download_cmd.typer, "echo", side_effect=lambda s: echoed.append(str(s))):
        download_cmd.emit_download_json_stdout(dl, None)
    data = json.loads(echoed[0])
    assert "download" in data
    assert "publish" not in data
    assert data["download"]["status"] == DownloadStatus.FAILED.value


def test_emit_download_json_stdout_includes_publish_when_present() -> None:
    dl = DownloadResult(
        url="https://u",
        status=DownloadStatus.SUCCESS,
        finished_at=datetime(2020, 1, 1),
    )
    pub = PublishResult(
        video_id="v",
        url="https://youtube.com/watch?v=v",
        title="t",
        privacy=PrivacyStatus.PUBLIC,
    )
    echoed: list[str] = []
    with patch.object(download_cmd.typer, "echo", side_effect=lambda s: echoed.append(str(s))):
        download_cmd.emit_download_json_stdout(dl, pub)
    data = json.loads(echoed[0])
    assert data["publish"]["video_id"] == "v"
