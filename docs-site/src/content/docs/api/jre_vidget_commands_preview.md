---
title: jre_vidget.commands.preview
description: "vidget preview command."
---


``vidget preview`` command.


#### preview

```python
def preview(url: str = typer.Argument(..., help="Video URL to preview"),
            json_output: bool = typer.Option(
                False,
                "--json",
                help="Output JSON only on stdout (for scripting).",
            )) -> None
```

Fetch and display video metadata without downloading.

