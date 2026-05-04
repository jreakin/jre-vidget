# ADR-005: Dockerized CLI Tool

**Date:** 2026-05-03
**Status:** Accepted
**Deciders:** jreakin

---

## Context

jre-vidget was designed as a local macOS CLI tool replacing iTube Studio. The goal is to
make it portable — usable from other projects via `git clone` without requiring Python,
yt-dlp, or ffmpeg to be installed on the host.

**Rejected approach:** wrapping the engine in a FastAPI HTTP server and deploying to
Railway. This added HTTP indirection, a job-polling workflow, and ongoing server costs
for what is fundamentally a command-line tool. The right tool for shell-script and
Makefile integration is a CLI, not an API.

---

## Decision

Ship jre-vidget as a self-contained Docker image with `ENTRYPOINT ["vidget"]`.

The image bundles Python 3.12, yt-dlp, and ffmpeg. Callers mount a host directory
at `/downloads` and pass CLI arguments directly — no HTTP, no polling, no server.

---

## Usage Pattern

```bash
# Clone once
git clone https://github.com/jreakin/jre-vidget

# Build once
docker build -t jre-vidget jre-vidget/

# Use anywhere — same flags as the native CLI
docker run --rm -v ~/Downloads:/downloads jre-vidget download "URL" --output /downloads
docker run --rm -v ~/Downloads:/downloads jre-vidget batch urls.txt --output /downloads
docker run --rm jre-vidget formats "URL" --json
```

## Integration in Other Projects

Two integration options are provided in `bin/`:

**`bin/vidget`** — shell wrapper script. Symlink or copy to PATH:
```bash
ln -s /path/to/jre-vidget/bin/vidget /usr/local/bin/vidget
vidget download "URL" --output ~/Downloads
```

**`bin/vidget.mk`** — Makefile include for project-level integration:
```makefile
VIDGET_DIR := /path/to/jre-vidget
include $(VIDGET_DIR)/bin/vidget.mk

download:
    make vidget-download URL="https://..." OUTPUT=./media
```

---

## Consequences

- Zero runtime dependencies on the host (only Docker required)
- Portable across macOS, Linux, and CI environments
- Output files written to a host-mounted volume — no data stays in the container
- No server to maintain, no API key management, no polling loop
- Build once, reuse across projects via git submodule or a simple clone
