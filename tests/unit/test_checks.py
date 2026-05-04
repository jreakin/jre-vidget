"""Unit tests for dependency pre-flight (``checks``)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import typer

from jre_vidget.checks import check_dependencies, verify_dependencies

pytestmark = pytest.mark.real_dependency_checks


def test_verify_dependencies_missing_yt_dlp_raises_exit_1(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with (
        patch("importlib.util.find_spec", return_value=None),
        pytest.raises(typer.Exit) as exc,
    ):
        verify_dependencies()
    assert exc.value.exit_code == 1
    err = capsys.readouterr().err
    assert "yt-dlp" in err


def test_verify_dependencies_missing_ffmpeg_warns_only(capsys: pytest.CaptureFixture[str]) -> None:
    with (
        patch("importlib.util.find_spec", return_value=object()),
        patch("shutil.which", return_value=None),
    ):
        verify_dependencies()
    err = capsys.readouterr().err
    assert "ffmpeg" in err


def test_verify_dependencies_all_present(capsys: pytest.CaptureFixture[str]) -> None:
    with (
        patch("importlib.util.find_spec", return_value=object()),
        patch("shutil.which", return_value="/usr/bin/ffmpeg"),
    ):
        verify_dependencies()
    assert capsys.readouterr().err == ""


def test_check_dependencies_delegates_same_as_verify(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``verify_dependencies`` is a thin alias; ``check_dependencies`` owns the body."""
    with (
        patch("importlib.util.find_spec", return_value=object()),
        patch("shutil.which", return_value="/usr/bin/ffmpeg"),
    ):
        check_dependencies()
    assert capsys.readouterr().err == ""
