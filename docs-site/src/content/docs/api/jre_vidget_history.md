---
title: jre_vidget.history
description: "Upload history file (uploads.json) — schema version and append helpers."
---


Upload history file (``uploads.json``) — schema version and append helpers.

Used by ``vidget history append`` and CI workflows instead of ad-hoc inline Python.

On POSIX, ``append_upload_record`` uses an exclusive whole-file lock during
read-modify-write so concurrent appends do not clobber each other. On other
platforms a temp-file replace is used (best-effort atomicity).


#### ensure\_uploads\_document

```python
def ensure_uploads_document(data: dict[str, Any]) -> dict[str, Any]
```

Normalize in-memory document shape.

Legacy files omit ``schemaVersion``; callers should persist after mutation so
``schemaVersion`` is written.


#### load\_uploads

```python
def load_uploads(path: Path) -> dict[str, Any]
```

Load ``uploads.json`` or return an empty document if the file is missing.


#### append\_upload\_record

```python
def append_upload_record(path: Path, *, video_id: str, title: str,
                         source_url: str, privacy: str,
                         run_id: str) -> dict[str, Any]
```

Prepend one upload row and persist.

Empty ``title`` (after strip) becomes ``"untitled"``, matching the GitHub
Actions workflow behavior.

