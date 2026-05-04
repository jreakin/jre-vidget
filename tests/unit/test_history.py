"""Tests for ``uploads.json`` history helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jre_vidget import history


def test_load_uploads_missing_file_returns_empty_with_schema(tmp_path: Path) -> None:
    path = tmp_path / "uploads.json"
    data = history.load_uploads(path)
    assert data["schemaVersion"] == history.UPLOADS_SCHEMA_VERSION
    assert data["uploads"] == []


def test_ensure_uploads_document_legacy_no_schema(tmp_path: Path) -> None:
    path = tmp_path / "uploads.json"
    path.write_text(json.dumps({"uploads": [{"video_id": "x"}]}), encoding="utf-8")
    data = history.load_uploads(path)
    assert data["schemaVersion"] == history.UPLOADS_SCHEMA_VERSION
    assert len(data["uploads"]) == 1
    assert data["uploads"][0]["video_id"] == "x"


def test_append_inserts_at_front_and_sets_schema(tmp_path: Path) -> None:
    path = tmp_path / "uploads.json"
    path.write_text(
        json.dumps({"uploads": [{"video_id": "old"}]}),
        encoding="utf-8",
    )
    history.append_upload_record(
        path,
        video_id="newid",
        title="Hello",
        source_url="https://src",
        privacy="public",
        run_id="42",
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schemaVersion"] == history.UPLOADS_SCHEMA_VERSION
    assert data["uploads"][0]["video_id"] == "newid"
    assert data["uploads"][0]["title"] == "Hello"
    assert data["uploads"][0]["source_url"] == "https://src"
    assert data["uploads"][0]["privacy"] == "public"
    assert data["uploads"][0]["run_id"] == "42"
    assert data["uploads"][0]["url"] == "https://youtube.com/watch?v=newid"
    assert data["uploads"][1]["video_id"] == "old"
    assert "uploaded_at" in data["uploads"][0]


def test_append_empty_title_becomes_untitled(tmp_path: Path) -> None:
    path = tmp_path / "uploads.json"
    history.append_upload_record(
        path,
        video_id="v",
        title="   ",
        source_url="https://u",
        privacy="unlisted",
        run_id="1",
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["uploads"][0]["title"] == "untitled"


def test_load_uploads_rejects_non_object(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[1,2]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        history.load_uploads(path)
