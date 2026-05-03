"""
Rich terminal UI — spinner, progress bar, tables, panels.

See prompts/phase-5-rich-ui.md for the full implementation spec.
"""

from __future__ import annotations

from rich.console import Console

from jre_vidget.engine import ProgressData, ProgressHook
from jre_vidget.models import DownloadResult, DownloadStatus

console = Console()


def make_progress_hook() -> ProgressHook:
    """Minimal yt-dlp progress hook; Phase 5 replaces with a Rich progress bar."""

    err_console = Console(stderr=True)

    def hook(d: ProgressData) -> None:
        if d.get("status") == "finished" and d.get("filename"):
            err_console.print(f"Finished: {d['filename']}", highlight=False)

    return hook


def print_result(result: DownloadResult) -> None:
    """One-line result for batch downloads (CLI delegates here)."""
    if result.status == DownloadStatus.SUCCESS:
        path = result.filepath if result.filepath is not None else "?"
        console.print(f"[green]OK[/green] {result.url} → {path}")
    else:
        err = result.error or "unknown error"
        console.print(f"[red]FAIL[/red] {result.url}: {err}")
