# ADR-005: Railway + Docker Deployment

**Date:** 2026-05-03
**Status:** Accepted
**Deciders:** jreakin

---

## Context

jre-vidget was designed as a local macOS CLI tool replacing iTube Studio. The goal is to
run downloads without being at the Mac — triggered from a phone, browser, or script.

**Rejected alternatives:**

| Option | Why rejected |
|--------|-------------|
| Cloudflare Workers | V8 JS/WASM isolates only — no Python, no subprocess, no ffmpeg |
| Google Cloud Functions | Same constraints; 9-minute max — insufficient for large videos |
| Google Cloud Run | Viable but requires async job queue design and GCS for storage |

Railway was chosen because it runs persistent Docker containers (not serverless), supports
long-running processes, provides persistent volumes, and has a simple deploy-from-Dockerfile
workflow with no platform-specific SDK.

---

## Decision

Deploy jre-vidget as a Docker container on Railway with a thin FastAPI HTTP API
(`src/jre_vidget/server.py`) layered on top of the existing engine.

The CLI layer (`cli.py`) is unchanged and continues to work for local macOS use.
The server is opt-in via a `[server]` extras group in `pyproject.toml`.

---

## API Design

Downloads take longer than HTTP timeouts, so the server uses the async job pattern:

```
POST /download      →  202 Accepted  { job_id: "uuid" }
GET  /jobs/{id}     →  200           { status: "pending|running|done|failed", filename? }
GET  /files/{name}  →  200           (file stream)
GET  /health        →  200           { ok: true }
```

Optional API key auth via `VIDGET_API_KEY` env var + `X-Api-Key` request header.

---

## File Storage

Files are written to `/downloads` inside the container, backed by a Railway persistent
volume (configured in the Railway dashboard after first deploy).

Files are **not** uploaded to S3/GCS — keeps the implementation dependency-free.
Adding S3 upload support later is straightforward: replace `FileResponse` with a
presigned-URL redirect in `GET /files/{filename}`.

---

## Job Store

In-memory Python dict. Adequate for single-instance Railway deployment.
Jobs are lost on container restart; files on the volume persist.

If multi-instance or job durability is needed later, the store can be swapped for
Redis (one dependency + env var change in `server.py`).

---

## Consequences

- Single-instance only (in-memory job store)
- Files persist across restarts via Railway volume mount at `/downloads`
- No S3/GCS dependency — simpler ops
- The CLI tool continues to work identically for local use
- `httpx` added to dev extras for FastAPI test client
