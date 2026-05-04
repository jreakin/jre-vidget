"""
Dependency pre-flight checks — yt-dlp importable, ffmpeg on PATH.

See prompts/phase-6-config-error-polish/current.md for the spec.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys

import typer


def check_dependencies() -> None:
    """
    CLI pre-flight: verify yt-dlp is importable; warn on stderr if ffmpeg is missing.

    Exits with code 1 if yt-dlp is not available.
    """
    if importlib.util.find_spec("yt_dlp") is None:
        sys.stderr.write(
            "❌  yt-dlp not found. Install with: pip install yt-dlp\n",
        )
        raise typer.Exit(code=1)

    if shutil.which("ffmpeg") is None:
        sys.stderr.write(
            "⚠️  ffmpeg not found — format conversion will not work.\n"
            "   Install with: brew install ffmpeg\n",
        )


def verify_dependencies() -> None:
    """Backward-compatible alias for :func:`check_dependencies`."""
    check_dependencies()
