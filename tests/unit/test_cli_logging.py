"""Tests for VIDGET_LOG_LEVEL wiring in the CLI."""

from __future__ import annotations

import logging

import pytest

from jre_vidget import cli as vidget_cli


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
