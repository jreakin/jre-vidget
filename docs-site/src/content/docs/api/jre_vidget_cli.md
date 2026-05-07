---
title: jre_vidget.cli
description: "Typer CLI entry — mounts download / batch / formats / preview / publish, nested config and auth groups, and history."
---


Typer CLI entry — mounts ``download`` / ``batch`` / ``formats`` / ``preview`` / ``publish``, nested ``config`` and ``auth`` groups, and ``history``.

Dependency checks run before most commands (see `jre_vidget.checks.check_dependencies`).


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

