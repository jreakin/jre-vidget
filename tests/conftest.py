"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _mock_dependency_checks(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Avoid pre-flight yt-dlp/ffmpeg checks during CLI tests."""
    # Unit tests for ``checks`` must run the real implementation (not a MagicMock).
    node_path = getattr(request.node, "path", None)
    if node_path is not None and node_path.name == "test_checks.py":
        yield
        return
    with patch("jre_vidget.checks.check_dependencies"):
        yield
