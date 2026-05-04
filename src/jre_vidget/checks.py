"""
Dependency pre-flight checks — yt-dlp importable, ffmpeg on PATH.

See prompts/phase-6-config-error-polish/current.md for the spec.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys

import typer


def verify_dependencies() -> None:
    """Verify yt-dlp is importable; warn on stderr if ffmpeg is missing. Exit 1 if yt-dlp absent."""
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


def check_dependencies() -> None:
    """CLI pre-flight; same checks as :func:`verify_dependencies`."""
    verify_dependencies()
