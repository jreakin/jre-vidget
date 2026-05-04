"""Unit tests for Rich UI helpers (``ui``)."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest
from pydantic import SecretStr
from rich.console import Console
from rich.progress import Progress

from jre_vidget import ui
from jre_vidget.models import (
    AppConfig,
    AuthConfig,
    DownloadResult,
    DownloadStatus,
    Quality,
    YtdlpStatus,
)


def test_config_secret_placeholder_none() -> None:
    assert ui._config_secret_placeholder(None) == "—"


def test_config_secret_placeholder_empty_secret() -> None:
    assert ui._config_secret_placeholder(SecretStr("")) == "—"


def test_config_secret_placeholder_set() -> None:
    assert ui._config_secret_placeholder(SecretStr("x")) == "(set)"


def test_print_config_uses_table(monkeypatch: pytest.MonkeyPatch) -> None:
    buf = StringIO()
    fake_console = Console(file=buf, width=120, force_terminal=True, color_system=None)
    monkeypatch.setattr(ui, "console", fake_console)
    cfg = AppConfig(
        output_dir=Path("/tmp/out"),
        quality=Quality.P720,
        subtitles=True,
        auth=AuthConfig(
            client_id="cid",
            client_secret=SecretStr("sec"),
            refresh_token=SecretStr("rt"),
        ),
    )
    ui.print_config(cfg)
    text = buf.getvalue()
    assert "output_dir" in text
    assert "/tmp/out" in text
    assert "720p" in text
    assert "(set)" in text


def test_print_result_success_line(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    buf = StringIO()
    monkeypatch.setattr(ui, "console", Console(file=buf, width=80, color_system=None))
    fp = tmp_path / "a.mp4"
    fp.touch()
    ui.print_result(
        DownloadResult(
            url="https://example.com",
            status=DownloadStatus.SUCCESS,
            filepath=fp,
            duration_s=1.5,
        )
    )
    out = buf.getvalue()
    assert "a.mp4" in out


def test_make_progress_hook_error_invokes_print_error(monkeypatch: pytest.MonkeyPatch) -> None:
    buf = StringIO()
    monkeypatch.setattr(ui, "console", Console(file=buf, width=80, color_system=None))
    captured: list[tuple[str, str | None]] = []

    def capture_error(title: str, detail: str | None = None) -> None:
        captured.append((title, detail))

    monkeypatch.setattr(ui, "print_error", capture_error)
    hook, progress = ui.make_progress_hook()
    with progress:
        hook({"status": YtdlpStatus.ERROR.value, "error": "network reset"})
    assert captured == [("Download error", "network reset")]


def test_make_progress_hook_downloading_then_finished(monkeypatch: pytest.MonkeyPatch) -> None:
    buf = StringIO()
    monkeypatch.setattr(
        ui,
        "console",
        Console(file=buf, width=120, force_terminal=True, color_system=None),
    )
    hook, progress = ui.make_progress_hook()
    with progress:
        hook(
            {
                "status": YtdlpStatus.DOWNLOADING.value,
                "filename": "/tmp/subdir/file.mp4",
                "downloaded_bytes": 0,
                "total_bytes": 100,
            }
        )
        hook({"status": YtdlpStatus.FINISHED.value, "filename": "/tmp/subdir/file.mp4"})
    out = buf.getvalue()
    assert "Merging" in out


def test_progress_tracker_on_error_without_progress_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``ProgressTracker`` may receive an error hook before any task exists."""
    buf = StringIO()
    monkeypatch.setattr(ui, "console", Console(file=buf, width=80, color_system=None))
    captured: list[tuple[str, str | None]] = []
    monkeypatch.setattr(ui, "print_error", lambda t, d=None: captured.append((t, d)))
    progress = Progress(console=Console(file=buf, width=80, color_system=None))
    tracker = ui.ProgressTracker(progress)
    tracker({"status": YtdlpStatus.ERROR.value, "error": "early"})
    assert captured == [("Download error", "early")]


def test_print_result_failed_panel(monkeypatch: pytest.MonkeyPatch) -> None:
    buf = StringIO()
    monkeypatch.setattr(ui, "console", Console(file=buf, width=80, color_system=None))
    ui.print_result(
        DownloadResult(
            url="https://example.com",
            status=DownloadStatus.FAILED,
            error="boom",
        )
    )
    assert "boom" in buf.getvalue()
