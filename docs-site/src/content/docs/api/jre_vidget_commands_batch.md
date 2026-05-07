---
title: jre_vidget.commands.batch
description: "vidget batch command."
---


``vidget batch`` command.


#### batch

```python
def batch(file: Path = typer.Argument(...,
                                      help="Text file with one URL per line"),
          quality: Quality | None = typer.Option(None, "--quality", "-q"),
          out_format: OutputFormat | None = typer.Option(
              None, "--format", "-f"),
          output: Path | None = typer.Option(None, "--output", "-o"),
          subs: bool | None = typer.Option(
              None,
              "--subs/--no-subs",
              help="Download subtitles (default: saved config).",
          ),
          json_output: bool = typer.Option(
              False,
              "--json",
              help="Emit only JSON on stdout (list of download results).",
          )) -> None
```

Download all URLs listed in a text file (one per line).

