---
title: jre_vidget.publish_flow
description: "Pure publish orchestration: title resolution and PublishConfig assembly (no Typer/Rich)."
---


Pure publish orchestration: title resolution and `PublishConfig` assembly (no Typer/Rich).


## PublishOptions Objects

```python
@dataclass(frozen=True)
class PublishOptions()
```

YouTube publish fields collected from the download command.


#### resolve\_publish\_title\_for\_download

```python
def resolve_publish_title_for_download(options: PublishOptions, *,
                                       video_info: VideoInfo | None,
                                       fallback_url: str) -> str
```

Pick title: explicit CLI title, else scraped title, else the source URL.


#### publish\_config\_for\_downloaded\_file

```python
def publish_config_for_downloaded_file(filepath: Path, options: PublishOptions,
                                       *, video_info: VideoInfo | None,
                                       url: str) -> PublishConfig
```

Build `PublishConfig` after a successful download.

