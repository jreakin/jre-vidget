"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _mock_dependency_checks() -> Generator[None, None, None]:
    """Avoid pre-flight yt-dlp/ffmpeg checks during CLI tests."""
    with patch("jre_vidget.checks.check_dependencies"):
        yield
