---
title: jre_vidget.cli
description: "Typer CLI — thin entry: mounts command groups and top-level commands."
---


Typer CLI — thin entry: mounts command groups and top-level commands.


#### main

```python
@app.callback()
def main(
    ctx: typer.Context,
    _version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
    )
) -> None
```

Global options; runs before every subcommand.

