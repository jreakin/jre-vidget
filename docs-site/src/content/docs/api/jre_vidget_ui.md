---
title: jre_vidget.ui
description: "Rich terminal UI — spinner, progress bar, tables, panels."
---


Rich terminal UI — spinner, progress bar, tables, panels.

See prompts/phase-5-rich-ui/current.md for the full implementation spec.


#### spinner

```python
@contextmanager
def spinner(message: str) -> Iterator[None]
```

Show a Rich spinner while a block executes.


#### print\_preview

```python
def print_preview(meta: VideoPreview) -> None
```

Render a Rich preview card for a VideoPreview.


#### print\_video\_info

```python
def print_video_info(info: VideoInfo) -> None
```

Header panel before download or format listing.


## ProgressTracker Objects

```python
class ProgressTracker()
```

Drive a Rich `~rich.progress.Progress` from yt-dlp ``progress_hooks``.


#### print\_formats\_table

```python
def print_formats_table(info: VideoInfo) -> None
```

Display available video and audio-only formats.


#### make\_progress\_hook

```python
def make_progress_hook() -> tuple[ProgressHook, Progress]
```

Return a (hook_fn, progress_context) tuple.

hook_fn is passed directly to yt-dlp's progress_hooks list.
progress_context is a Rich Progress instance the caller should use
as a context manager.


#### print\_result

```python
def print_result(result: DownloadResult) -> None
```

Print outcome of one download (single or batch live line).


#### print\_batch\_summary

```python
def print_batch_summary(job: BatchJob) -> None
```

Final summary table after a batch run.


#### print\_config

```python
def print_config(config: AppConfig) -> None
```

Show config as a styled table.


#### print\_error

```python
def print_error(message: str, detail: str | None = None) -> None
```

Styled error panel.


#### print\_warning

```python
def print_warning(message: str) -> None
```

Non-fatal warning line.


#### print\_success

```python
def print_success(message: str) -> None
```

Success confirmation line.


#### print\_batch\_intro

```python
def print_batch_intro(count: int) -> None
```

Announce how many URLs were read for batch.

