---
title: jre_vidget.models
description: "Pydantic v2 data models for jre-vidget."
---


Pydantic v2 data models for jre-vidget.

Shared between the CLI, engine, and UI. Validation and serialization only.


## YtdlpStatus Objects

```python
class YtdlpStatus(StrEnum)
```

yt-dlp ``progress_hooks`` payload ``status`` values handled in engine / UI.

yt-dlp may emit other statuses (e.g. post-processing); those are ignored so
hooks stay a no-op unless they match one of these values.


## Quality Objects

```python
class Quality(StrEnum)
```

Supported download quality presets.


## OutputFormat Objects

```python
class OutputFormat(StrEnum)
```

Supported output container / codec targets.


## VideoFormat Objects

```python
class VideoFormat(BaseModel)
```

One available stream format from yt-dlp.


## DownloadError Objects

```python
class DownloadError(Exception)
```

Metadata extraction failed (preview / probe) — wraps yt-dlp extract errors.


## VideoPreview Objects

```python
class VideoPreview(BaseModel)
```

Metadata fetched before download — used to confirm before upload.


#### upload\_date

YYYYMMDD string from yt-dlp


#### formats

e.g. ["1080p60", "720p", "480p"]


#### duration\_display

```python
@property
def duration_display() -> str
```

Return HH:MM:SS or MM:SS string.


## VideoInfo Objects

```python
class VideoInfo(BaseModel)
```

Metadata for a single URL from yt-dlp.


#### best\_formats

```python
@property
def best_formats() -> list[VideoFormat]
```

Distinct-resolution video formats, sorted best-first by bitrate.


## DownloadConfig Objects

```python
class DownloadConfig(BaseModel)
```

Options for a single download job.


## AuthConfig Objects

```python
class AuthConfig(BaseModel)
```

YouTube OAuth credentials — persisted inside AppConfig.


## PrivacyStatus Objects

```python
class PrivacyStatus(StrEnum)
```

YouTube video privacy — matches Data API ``status.privacyStatus`` values.


## PublishConfig Objects

```python
class PublishConfig(BaseModel)
```

Options for a single YouTube upload job.


#### title

required — no default


## PublishResult Objects

```python
class PublishResult(BaseModel)
```

Outcome of a completed YouTube upload.


#### url

https://youtube.com/watch?v=...


## AppConfig Objects

```python
class AppConfig(BaseModel)
```

User preference shape for ``~/.vidget/config.json`` (read/write via ``jre_vidget.config``).


## DownloadStatus Objects

```python
class DownloadStatus(StrEnum)
```

Terminal status of a download attempt.


## DownloadResult Objects

```python
class DownloadResult(BaseModel)
```

Outcome of a completed download job.


## BatchJob Objects

```python
class BatchJob(BaseModel)
```

Batch of URLs using one DownloadConfig.

