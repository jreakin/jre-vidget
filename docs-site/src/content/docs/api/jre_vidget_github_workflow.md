---
title: jre_vidget.github_workflow
description: "GitHub Actions workflow dispatch (gh CLI) — isolated from Typer/Rich helpers."
---


GitHub Actions workflow dispatch (``gh`` CLI) — isolated from Typer/Rich helpers.


#### dispatch\_publish\_workflow

```python
def dispatch_publish_workflow(*, url: str, title: str, description: str,
                              privacy: PrivacyStatus,
                              remove_after_upload: bool) -> None
```

Trigger ``publish.yml`` via the GitHub CLI (``gh`` must be installed and authenticated).

