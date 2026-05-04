"""Tests for VIDGET_LOG_LEVEL wiring in the CLI."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

import pytest

from jre_vidget import cli_common as vidget_cli

_REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _reset_logging_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VIDGET_LOG_LEVEL", raising=False)


def test_log_level_from_env_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VIDGET_LOG_LEVEL", raising=False)
    assert vidget_cli._log_level_from_env() == logging.WARNING


def test_log_level_from_env_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VIDGET_LOG_LEVEL", "debug")
    assert vidget_cli._log_level_from_env() == logging.DEBUG


def test_log_level_from_env_invalid_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VIDGET_LOG_LEVEL", "not-a-real-level")
    assert vidget_cli._log_level_from_env() == logging.WARNING


def test_log_level_from_env_empty_uses_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VIDGET_LOG_LEVEL", "   ")
    assert vidget_cli._log_level_from_env() == logging.WARNING


def test_json_line_formatter_emits_one_json_object_per_line() -> None:
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    line = vidget_cli._JsonLineFormatter().format(record)
    data = json.loads(line)
    assert data["level"] == "INFO"
    assert data["logger"] == "test.logger"
    assert data["message"] == "hello"


def test_ensure_cli_logging_json_format_writes_parseable_lines_to_stderr() -> None:
    """End-to-end: fresh process, clean root logger, JSON formatter on stderr."""
    code = r"""
import logging
import os

os.environ["VIDGET_LOG_FORMAT"] = "json"
os.environ["VIDGET_LOG_LEVEL"] = "INFO"
root = logging.getLogger()
root.handlers.clear()
root.setLevel(logging.NOTSET)

from jre_vidget.cli_common import ensure_cli_logging

ensure_cli_logging()
logging.getLogger("vidget.subprocess_json_test").warning("marker-for-json-test")
"""
    result = subprocess.run(
        ["uv", "run", "python", "-c", code],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    found = False
    for line in (result.stderr or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if data.get("message") == "marker-for-json-test" and data.get("level") == "WARNING":
            found = True
            break
    assert found, result.stderr
