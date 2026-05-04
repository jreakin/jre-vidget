# Architecture Decision Records (jre-vidget)

Short, decision-focused notes. Each ADR is a standalone markdown file in this directory.

| File | Topic |
|------|--------|
| [ADR-001-yt-dlp-for-extraction.md](ADR-001-yt-dlp-for-extraction.md) | yt-dlp as the download / metadata boundary |
| [ADR-002-typer-cli-framework.md](ADR-002-typer-cli-framework.md) | Typer for the `vidget` CLI |
| [ADR-003-pydantic-v2-models.md](ADR-003-pydantic-v2-models.md) | Pydantic v2 for config and API-shaped models |
| [ADR-004-ffmpeg-python-wrapper.md](ADR-004-ffmpeg-python-wrapper.md) | ffmpeg-python vs raw subprocess for ffmpeg |
| [ADR-005-railway-docker-deployment.md](ADR-005-railway-docker-deployment.md) | Container / Railway deployment notes |

For the full system picture, see [ARCHITECTURE.md](../../ARCHITECTURE.md) and [AGENTS.md](../../AGENTS.md).
