"""Tests for ``uploads.json`` history helpers."""

from __future__ import annotations

import json
import threading
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


def test_load_uploads_uploads_null_becomes_empty_list(tmp_path: Path) -> None:
    path = tmp_path / "uploads.json"
    path.write_text(json.dumps({"uploads": None, "schemaVersion": 1}), encoding="utf-8")
    data = history.load_uploads(path)
    assert data["uploads"] == []


def test_load_uploads_rejects_uploads_not_array(tmp_path: Path) -> None:
    path = tmp_path / "uploads.json"
    path.write_text(json.dumps({"uploads": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match="JSON array"):
        history.load_uploads(path)


def test_append_rejects_blank_video_id(tmp_path: Path) -> None:
    path = tmp_path / "uploads.json"
    with pytest.raises(ValueError, match="video_id"):
        history.append_upload_record(
            path,
            video_id="   ",
            title="t",
            source_url="https://u",
            privacy="public",
            run_id="1",
        )


@pytest.mark.skipif(history.fcntl is None, reason="whole-file locking uses fcntl (POSIX)")
def test_concurrent_appends_preserve_all_rows(tmp_path: Path) -> None:
    path = tmp_path / "uploads.json"
    path.write_text(
        json.dumps({"uploads": [{"video_id": "seed"}]}),
        encoding="utf-8",
    )
    barrier = threading.Barrier(5)
    errors: list[BaseException] = []

    def worker(i: int) -> None:
        try:
            barrier.wait()
            history.append_upload_record(
                path,
                video_id=f"tid{i}",
                title="t",
                source_url="https://u",
                privacy="public",
                run_id=str(i),
            )
        except BaseException as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data["uploads"]) == 6
    ids = {row["video_id"] for row in data["uploads"]}
    assert ids == {"seed", "tid0", "tid1", "tid2", "tid3", "tid4"}
