---
title: jre_vidget.commands.formats
description: "vidget formats command."
---


``vidget formats`` command.


#### formats

```python
def formats(url: str = typer.Argument(..., help="Video page URL to inspect"),
            json_output: bool = typer.Option(
                False,
                "--json",
                help="Emit only JSON on stdout (VideoInfo).",
            )) -> None
```

List available formats for a URL.

