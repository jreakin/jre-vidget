"""CLI tests for preview and URL-based publish (Actions dispatch)."""

from __future__ import annotations

import json
from unittest.mock import patch

from typer.testing import CliRunner

from jre_vidget.cli import app
from jre_vidget.models import DownloadError, VideoPreview

runner = CliRunner()

FAKE_PREVIEW = VideoPreview(
    url="https://youtube.com/watch?v=abc123",
    title="JRE #1234",
    description="An episode.",
    duration_seconds=3600,
    thumbnail_url="https://i.ytimg.com/vi/abc123/maxresdefault.jpg",
    uploader="PowerfulJRE",
)


def test_preview_command_renders_card() -> None:
    with patch("jre_vidget.cli.engine.preview", return_value=FAKE_PREVIEW):
        result = runner.invoke(app, ["preview", "https://youtube.com/watch?v=abc123"])
    assert result.exit_code == 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "JRE #1234" in combined
    assert "PowerfulJRE" in combined


def test_preview_command_json_flag() -> None:
    with patch("jre_vidget.cli.engine.preview", return_value=FAKE_PREVIEW):
        result = runner.invoke(app, ["preview", "--json", "https://youtube.com/watch?v=abc123"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["title"] == "JRE #1234"


def test_preview_command_exits_1_on_error() -> None:
    with patch("jre_vidget.cli.engine.preview", side_effect=DownloadError("bad url")):
        result = runner.invoke(app, ["preview", "https://bad.url"])
    assert result.exit_code == 1


def test_publish_shows_preview_before_dispatching() -> None:
    dispatched: list[dict[str, object]] = []

    def fake_dispatch(**kwargs: object) -> None:
        dispatched.append(kwargs)

    with (
        patch("jre_vidget.cli.engine.preview", return_value=FAKE_PREVIEW),
        patch("jre_vidget.cli._dispatch_publish_workflow", side_effect=fake_dispatch),
    ):
        result = runner.invoke(
            app,
            ["publish", "--yes", "https://youtube.com/watch?v=abc123"],
        )

    assert result.exit_code == 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "JRE #1234" in combined
    assert len(dispatched) == 1


def test_publish_cancelled_when_not_confirmed() -> None:
    """TTY-style confirm path (CliRunner is non-TTY; simulate interactive)."""
    with (
        patch("jre_vidget.cli.engine.preview", return_value=FAKE_PREVIEW),
        patch("jre_vidget.cli._is_headless", return_value=False),
    ):
        result = runner.invoke(
            app,
            ["publish", "https://youtube.com/watch?v=abc123"],
            input="n\n",
        )
    assert result.exit_code == 0
    combined = (result.stdout or "").lower() + (result.stderr or "").lower()
    assert "cancelled" in combined


def test_publish_url_headless_requires_yes() -> None:
    with patch("jre_vidget.cli.engine.preview", return_value=FAKE_PREVIEW):
        result = runner.invoke(app, ["publish", "https://youtube.com/watch?v=abc123"])
    assert result.exit_code == 2
    combined = (result.stdout or "") + (result.stderr or "")
    assert "non-interactive" in combined.lower()
    assert "--yes" in combined.lower()
