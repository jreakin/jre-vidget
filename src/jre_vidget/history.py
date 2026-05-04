"""
Upload history file (``uploads.json``) — schema version and append helpers.

Used by ``vidget history append`` and CI workflows instead of ad-hoc inline Python.

On POSIX, ``append_upload_record`` uses an exclusive whole-file lock during
read-modify-write so concurrent appends do not clobber each other. On other
platforms a temp-file replace is used (best-effort atomicity).
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

fcntl: Any
try:
    import fcntl as _fcntl_impl
except ImportError:
    fcntl = None  # Windows — use temp-file replace path instead of flock
else:
    fcntl = _fcntl_impl

UPLOADS_SCHEMA_VERSION = 1


def _coerce_uploads_list(data: dict[str, Any]) -> None:
    """
    Ensure ``data['uploads']`` is a list.

    Raises :class:`ValueError` if ``uploads`` is present but not an array (avoids
    silently wiping malformed history on the next save). ``null`` is treated as
    an empty list.
    """
    if "uploads" not in data:
        data["uploads"] = []
        return
    raw = data["uploads"]
    if raw is None:
        data["uploads"] = []
        return
    if isinstance(raw, list):
        return
    got = type(raw).__name__
    msg = f"top-level 'uploads' must be a JSON array, not {got}"
    raise ValueError(msg)


def ensure_uploads_document(data: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize in-memory document shape.

    Legacy files omit ``schemaVersion``; callers should persist after mutation so
    ``schemaVersion`` is written.
    """
    out: dict[str, Any] = dict(data)
    _coerce_uploads_list(out)
    if "schemaVersion" not in out:
        out["schemaVersion"] = UPLOADS_SCHEMA_VERSION
    return out


def _document_from_raw(raw: str) -> dict[str, Any]:
    """Parse file body into a normalized document dict."""
    if not raw.strip():
        return {"schemaVersion": UPLOADS_SCHEMA_VERSION, "uploads": []}
    parsed: Any = json.loads(raw)
    if not isinstance(parsed, dict):
        msg = "uploads file must contain a JSON object at the top level"
        raise ValueError(msg)
    return ensure_uploads_document(parsed)


def load_uploads(path: Path) -> dict[str, Any]:
    """Load ``uploads.json`` or return an empty document if the file is missing."""
    if not path.exists():
        return {"schemaVersion": UPLOADS_SCHEMA_VERSION, "uploads": []}
    return _document_from_raw(path.read_text(encoding="utf-8"))


def _utc_iso_z() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def build_youtube_watch_url(video_id: str) -> str:
    """Canonical watch URL stored in history (matches prior workflow output)."""
    return f"https://youtube.com/watch?v={video_id}"


def _build_record(
    *,
    video_id: str,
    title: str,
    source_url: str,
    privacy: str,
    run_id: str,
) -> dict[str, Any]:
    vid = video_id.strip()
    if not vid:
        msg = "video_id must be a non-empty string"
        raise ValueError(msg)
    src = source_url.strip()
    if not src:
        msg = "source_url must be a non-empty string"
        raise ValueError(msg)
    rid = run_id.strip()
    if not rid:
        msg = "run_id must be a non-empty string"
        raise ValueError(msg)
    effective_title = title.strip() if title.strip() else "untitled"
    return {
        "video_id": vid,
        "url": build_youtube_watch_url(vid),
        "title": effective_title,
        "source_url": src,
        "privacy": privacy,
        "uploaded_at": _utc_iso_z(),
        "run_id": rid,
    }


def _insert_record_and_serialize(data: dict[str, Any], record: dict[str, Any]) -> str:
    uploads = data["uploads"]
    if not isinstance(uploads, list):
        msg = "internal error: uploads must be a list after normalization"
        raise TypeError(msg)
    uploads.insert(0, record)
    data["schemaVersion"] = UPLOADS_SCHEMA_VERSION
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _append_via_temp_replace(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Read-modify-write using a temp file and replace (non-POSIX or fallback)."""
    data = load_uploads(path)
    serialized = _insert_record_and_serialize(data, record)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(serialized, encoding="utf-8")
    tmp.replace(path)
    return record


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
    Prepend one upload row and persist.

    Empty ``title`` (after strip) becomes ``\"untitled\"``, matching the GitHub
    Actions workflow behavior.
    """
    record = _build_record(
        video_id=video_id,
        title=title,
        source_url=source_url,
        privacy=privacy,
        run_id=run_id,
    )

    if fcntl is None:
        return _append_via_temp_replace(path, record)

    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            json.dumps(
                {"schemaVersion": UPLOADS_SCHEMA_VERSION, "uploads": []},
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

    with open(path, "r+", encoding="utf-8") as fp:
        fcntl.flock(fp, fcntl.LOCK_EX)
        try:
            raw = fp.read()
            data = _document_from_raw(raw)
            serialized = _insert_record_and_serialize(data, record)
            fp.seek(0)
            fp.write(serialized)
            fp.truncate()
            fp.flush()
            os.fsync(fp.fileno())
        finally:
            fcntl.flock(fp, fcntl.LOCK_UN)
    return record
