---
title: jre_vidget.commands.config_cmd
description: "vidget config subcommands."
---


``vidget config`` subcommands.


#### config\_show

```python
def config_show() -> None
```

Print current saved configuration.


#### config\_set

```python
def config_set(output: Path | None = typer.Option(
    None, "--output", help="Default output directory"),
               quality: Quality | None = typer.Option(None,
                                                      "--quality",
                                                      help="Default quality"),
               out_format: OutputFormat | None = typer.Option(
                   None,
                   "--format",
                   help="Default output format",
               ),
               subs: bool | None = typer.Option(None,
                                                "--subs/--no-subs")) -> None
```

Update stored defaults (only specified options change).


#### config\_reset

```python
def config_reset(yes: bool = typer.Option(
    False, "--yes", help="Skip confirmation prompt")) -> None
```

Reset all settings to defaults.

