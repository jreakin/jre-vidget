FROM python:3.12-slim

# ---------------------------------------------------------------------------
# System dependencies — ffmpeg required for HLS stream merging via yt-dlp
# ---------------------------------------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------------------------------------------------------------------------
# Install the package — copy metadata first for better layer caching.
# Changing source files won't invalidate the pip install layer.
# ---------------------------------------------------------------------------
COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

# ---------------------------------------------------------------------------
# Runtime
# Mount a host directory here to receive downloaded files:
#   docker run --rm -v ~/Downloads:/downloads jre-vidget download URL --output /downloads
# ---------------------------------------------------------------------------
VOLUME /downloads

ENTRYPOINT ["vidget"]
CMD ["--help"]
