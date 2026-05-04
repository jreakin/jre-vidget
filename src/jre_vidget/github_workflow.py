"""GitHub Actions workflow dispatch (``gh`` CLI) — isolated from Typer/Rich helpers."""

from __future__ import annotations

import subprocess

from jre_vidget.models import PrivacyStatus


def dispatch_publish_workflow(
    *,
    url: str,
    title: str,
    description: str,
    privacy: PrivacyStatus,
    remove_after_upload: bool,
) -> None:
    """Trigger ``publish.yml`` via the GitHub CLI (``gh`` must be installed and authenticated)."""
    cmd = [
        "gh",
        "workflow",
        "run",
        "publish.yml",
        "-f",
        f"url={url}",
        "-f",
        f"title={title}",
        "-f",
        f"description={description}",
        "-f",
        f"privacy={privacy.value}",
        "-f",
        f"remove_after_upload={'true' if remove_after_upload else 'false'}",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError as e:
        msg = "Install the GitHub CLI (https://cli.github.com/) and ensure it is on PATH."
        raise RuntimeError(msg) from e
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or e.stdout or "").strip() or str(e)
        raise RuntimeError(detail) from e


__all__ = ["dispatch_publish_workflow"]
