---
title: jre_vidget.checks
description: "Dependency pre-flight checks — yt-dlp importable, ffmpeg on PATH."
---


Dependency pre-flight checks — yt-dlp importable, ffmpeg on PATH.

See prompts/phase-6-config-error-polish/current.md for the spec.


#### check\_dependencies

```python
def check_dependencies() -> None
```

CLI pre-flight: verify yt-dlp is importable; warn on stderr if ffmpeg is missing.

Exits with code 1 if yt-dlp is not available.


#### verify\_dependencies

```python
def verify_dependencies() -> None
```

Backward-compatible alias for `check_dependencies`.

