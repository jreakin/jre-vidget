"""Pure publish orchestration: title resolution and :class:`PublishConfig` assembly (no Typer/Rich)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jre_vidget.models import PrivacyStatus, PublishConfig, VideoInfo


@dataclass(frozen=True)
class PublishOptions:
    """YouTube publish fields collected from the download command."""

    title: str | None
    description: str
    privacy: PrivacyStatus
    remove_after_upload: bool


def resolve_publish_title_for_download(
    options: PublishOptions,
    *,
    video_info: VideoInfo | None,
    fallback_url: str,
) -> str:
    """Pick title: explicit CLI title, else scraped title, else the source URL."""
    if options.title:
        return options.title
    if video_info is not None:
        return video_info.title
    return fallback_url


def publish_config_for_downloaded_file(
    filepath: Path,
    options: PublishOptions,
    *,
    video_info: VideoInfo | None,
    url: str,
) -> PublishConfig:
    """Build :class:`PublishConfig` after a successful download."""
    title = resolve_publish_title_for_download(
        options,
        video_info=video_info,
        fallback_url=url,
    )
    return PublishConfig(
        filepath=filepath,
        title=title,
        description=options.description,
        privacy=options.privacy,
        remove_after_upload=options.remove_after_upload,
    )


__all__ = [
    "PublishOptions",
    "publish_config_for_downloaded_file",
    "resolve_publish_title_for_download",
]
