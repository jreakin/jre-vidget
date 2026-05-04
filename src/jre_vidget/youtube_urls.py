"""Small YouTube URL helpers shared by upload, history, and workflows."""

from __future__ import annotations


def build_youtube_watch_url(video_id: str) -> str:
    """Canonical watch URL stored in history (matches prior workflow output)."""
    return f"https://youtube.com/watch?v={video_id}"
