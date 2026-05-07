---
title: jre_vidget.publisher
description: "YouTube Data API v3 upload wrapper for jre-vidget."
---


YouTube Data API v3 upload wrapper for jre-vidget.

Pure upload logic — no CLI, no Rich, no auth management.
Mirrors engine.py in structure.

Public API:
  upload(config, auth, progress_hook=None) -> PublishResult


#### UploadProgressHook

(bytes_uploaded, total_bytes)


## PublishError Objects

```python
class PublishError(Exception)
```

Raised when the YouTube API rejects the upload or returns an error.


#### upload

```python
def upload(config: PublishConfig,
           auth_config: AuthConfig,
           progress_hook: UploadProgressHook | None = None) -> PublishResult
```

Upload a local video file to YouTube.

Steps:
1. Verify the file exists
2. Get valid credentials via auth.get_credentials()
3. Build MediaFileUpload with resumable=True
4. Call youtube.videos().insert() with metadata from config
5. Drive next_chunk() loop, calling progress_hook after each chunk
6. On success → return PublishResult
7. If remove_after_upload → delete local file ONLY after video_id confirmed
8. On HttpError → raise PublishError with API message

**Raises**:

- `PublishError` - file not found, API rejection, or unexpected error
- `AuthError` - re-raised from auth.get_credentials() if not authenticated

