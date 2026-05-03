import typer
from rich.console import Console

app = typer.Typer(
    name="vidget",
    help="🎬  Download & convert videos from 1000+ sites.",
    add_completion=False,
)
console = Console()


@app.command()
def download(url: str = typer.Argument(..., help="Video URL to download")) -> None:
    """Download a single video."""
    console.print(f"[bold green]Phase 1 stub:[/] would download {url}")


if __name__ == "__main__":
    app()
