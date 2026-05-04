"""
Upload history file (``uploads.json``) — schema version and append helpers.

Used by ``vidget history append`` and CI workflows instead of ad-hoc inline Python.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

UPLOADS_SCHEMA_VERSION = 1


def ensure_uploads_document(data: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize in-memory document shape.

    Legacy files omit ``schemaVersion``; callers should persist after mutation so
    ``schemaVersion`` is written.
    """
    out: dict[str, Any] = dict(data)
    raw_uploads = out.get("uploads")
    if not isinstance(raw_uploads, list):
        out["uploads"] = []
    if "schemaVersion" not in out:
        out["schemaVersion"] = UPLOADS_SCHEMA_VERSION
    return out


def load_uploads(path: Path) -> dict[str, Any]:
    """Load ``uploads.json`` or return an empty document if the file is missing."""
    if not path.exists():
        return {"schemaVersion": UPLOADS_SCHEMA_VERSION, "uploads": []}
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = "uploads file must contain a JSON object at the top level"
        raise ValueError(msg)
    return ensure_uploads_document(raw)


def _utc_iso_z() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def build_youtube_watch_url(video_id: str) -> str:
    """Canonical watch URL stored in history (matches prior workflow output)."""
    return f"https://youtube.com/watch?v={video_id}"


def append_upload_record(
    path: Path,
    *,
    video_id: str,
    title: str,
    source_url: str,
    privacy: str,
    run_id: str,
) -> dict[str, Any]:
    """
    Prepend one upload row and write ``path`` atomically (write + replace).

    Empty ``title`` (after strip) becomes ``\"untitled\"``, matching the GitHub
    Actions workflow behavior.
    """
    data = load_uploads(path)
    effective_title = title.strip() if title.strip() else "untitled"
    record: dict[str, Any] = {
        "video_id": video_id,
        "url": build_youtube_watch_url(video_id),
        "title": effective_title,
        "source_url": source_url,
        "privacy": privacy,
        "uploaded_at": _utc_iso_z(),
        "run_id": run_id,
    }
    uploads_raw = data["uploads"]
    if not isinstance(uploads_raw, list):
        uploads_raw = []
        data["uploads"] = uploads_raw
    uploads_raw.insert(0, record)
    data["schemaVersion"] = UPLOADS_SCHEMA_VERSION
    serialized = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(serialized, encoding="utf-8")
    tmp.replace(path)
    return record
