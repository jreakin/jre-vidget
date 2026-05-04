"""Unit tests for Rich UI helpers (``ui``)."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest
from pydantic import SecretStr
from rich.console import Console

from jre_vidget import ui
from jre_vidget.models import AppConfig, AuthConfig, DownloadResult, DownloadStatus, Quality


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
