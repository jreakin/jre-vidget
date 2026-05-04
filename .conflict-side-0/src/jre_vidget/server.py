"""
HTTP API server for jre-vidget.

Thin FastAPI wrapper over the download engine for cloud/remote operation.

Endpoints:
  POST /download           Submit a download job (returns job_id immediately)
  GET  /jobs/{job_id}      Poll status: pending → running → done | failed
  GET  /files/{filename}   Stream a completed file to the caller
  GET  /health             Railway health check

Deploy locally:
  uvicorn jre_vidget.server:app --reload --port 8000

Environment variables:
  DOWNLOADS_DIR    Where files are written (default: /downloads)
  VIDGET_API_KEY   Optional API key — if set, all endpoints require X-Api-Key header
  PORT             Injected by Railway at runtime
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from jre_vidget import engine
from jre_vidget.models import (
    DownloadConfig,
    DownloadResult,
    DownloadStatus,
    OutputFormat,
    Quality,
)

# ---------------------------------------------------------------------------
# Runtime config
# ---------------------------------------------------------------------------
DOWNLOADS_DIR = Path(os.getenv("DOWNLOADS_DIR", "/downloads"))
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

API_KEY: str | None = os.getenv("VIDGET_API_KEY")  # None = no auth required

app = FastAPI(
    title="vidget",
    version="0.1.0",
    description="Remote video downloader — POST a URL, poll for status, fetch the file.",
)

# ---------------------------------------------------------------------------
# In-memory job store
# Adequate for single-instance Railway deployment.
# Jobs are lost on container restart; files on the mounted volume persist.
# ---------------------------------------------------------------------------
JobStatus = Literal["pending", "running", "done", "failed"]


class _Job(BaseModel):
    id: str
    url: str
    status: JobStatus = "pending"
    filepath: str | None = None
    filename: str | None = None
    error: str | None = None


_jobs: dict[str, _Job] = {}


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------
def _require_auth(x_api_key: str | None) -> None:
    if API_KEY is not None and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Api-Key header")


# ---------------------------------------------------------------------------
# Request / response schemas (follow the envelope from ARCHITECTURE.md)
# ---------------------------------------------------------------------------
class DownloadRequest(BaseModel):
    url: str
    quality: Quality = Quality.BEST
    format: OutputFormat = OutputFormat.MP4
    subtitles: bool = False


class DownloadAccepted(BaseModel):
    ok: bool = True
    schema_version: int = 1
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    ok: bool = True
    schema_version: int = 1
    job_id: str
    url: str
    status: JobStatus
    filename: str | None = None  # set when status == "done"
    error: str | None = None  # set when status == "failed"


# ---------------------------------------------------------------------------
# Background download worker
# ---------------------------------------------------------------------------
def _run_download(job_id: str, request: DownloadRequest) -> None:
    job = _jobs[job_id]
    job.status = "running"
    try:
        config = DownloadConfig(
            url=request.url,
            output_dir=DOWNLOADS_DIR,
            quality=request.quality,
            format=request.format,
            subtitles=request.subtitles,
        )
        result: DownloadResult = engine.download(config)

        if result.status == DownloadStatus.SUCCESS and result.filepath:
            job.status = "done"
            job.filepath = str(result.filepath)
            job.filename = Path(result.filepath).name
        else:
            job.status = "failed"
            job.error = result.error or "Download failed with no error message"

    except engine.EngineError as exc:
        job.status = "failed"
        job.error = str(exc)
    except Exception as exc:  # noqa: BLE001 — surface all errors as job failures
        job.status = "failed"
        job.error = f"Unexpected error: {exc}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> dict:
    """Railway health check — always returns 200 if the server is up."""
    return {
        "ok": True,
        "version": "0.1.0",
        "downloads_dir": str(DOWNLOADS_DIR),
        "active_jobs": len(_jobs),
    }


@app.post("/download", response_model=DownloadAccepted, status_code=202)
def start_download(
    request: DownloadRequest,
    background_tasks: BackgroundTasks,
    x_api_key: str | None = Header(default=None),
) -> DownloadAccepted:
    """
    Submit a video download job.

    Returns 202 Accepted immediately with a job_id.
    Poll GET /jobs/{job_id} until status is 'done' or 'failed'.
    """
    _require_auth(x_api_key)
    job_id = str(uuid.uuid4())
    _jobs[job_id] = _Job(id=job_id, url=request.url)
    background_tasks.add_task(_run_download, job_id, request)
    return DownloadAccepted(job_id=job_id, status="pending")


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(
    job_id: str,
    x_api_key: str | None = Header(default=None),
) -> JobStatusResponse:
    """
    Poll download job status.

    When status == 'done', use the returned filename with GET /files/{filename}.
    """
    _require_auth(x_api_key)
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = _jobs[job_id]
    return JobStatusResponse(
        job_id=job.id,
        url=job.url,
        status=job.status,
        filename=job.filename,
        error=job.error,
    )


@app.get("/files/{filename}")
def get_file(
    filename: str,
    x_api_key: str | None = Header(default=None),
) -> FileResponse:
    """
    Stream a completed download file.

    filename comes from GET /jobs/{job_id} → filename field.
    """
    _require_auth(x_api_key)

    # Path traversal guard — resolve and verify the file is inside DOWNLOADS_DIR
    try:
        resolved = (DOWNLOADS_DIR / filename).resolve()
        resolved.relative_to(DOWNLOADS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=resolved, filename=filename)
