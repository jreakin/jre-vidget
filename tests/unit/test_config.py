"""Unit tests for jre_vidget.config."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from jre_vidget import config as vidget_config
from jre_vidget.models import AppConfig


@pytest.mark.skipif(os.name != "posix", reason="chmod mode bits are POSIX-specific")
def test_save_app_config_sets_restrictive_mode_bits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cfg_path = tmp_path / "home" / ".vidget" / "config.json"
    monkeypatch.setattr(vidget_config, "CONFIG_PATH", cfg_path)
    vidget_config.save_app_config(AppConfig())
    assert stat.S_IMODE(cfg_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(cfg_path.parent.stat().st_mode) == 0o700
