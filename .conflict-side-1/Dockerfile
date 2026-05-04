FROM python:3.12-slim

# ---------------------------------------------------------------------------
# System dependencies — ffmpeg is required for HLS stream merging via yt-dlp
# ---------------------------------------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------------------------------------------------------------------------
# Python dependencies — copy metadata first for better layer caching.
# A change to source code won't invalidate the pip install layer.
# ---------------------------------------------------------------------------
COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir ".[server]"

# ---------------------------------------------------------------------------
# Runtime setup
# ---------------------------------------------------------------------------
# /downloads is mounted as a Railway persistent volume — files survive restarts
RUN mkdir -p /downloads

ENV DOWNLOADS_DIR=/downloads

# Railway injects PORT at runtime; default to 8000 for local docker run
EXPOSE 8000

CMD ["sh", "-c", "uvicorn jre_vidget.server:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
