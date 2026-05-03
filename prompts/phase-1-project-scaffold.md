# Phase 1 — Project Scaffold

## Goal
Bootstrap the `jre-vidget` project with the correct folder structure, dependency
configuration, and entry point. No business logic yet — just a clean, runnable shell.

---

## Tech Stack
| Concern | Library |
|---------|---------|
| CLI framework | `typer[all]` |
| Terminal UI | `rich` |
| Data models | `pydantic` v2 |
| Video downloading | `yt-dlp` |
| Media conversion | `ffmpeg-python` |
| Python version | 3.11+ |

---

## Deliverables

### 1. `pyproject.toml`
Use `[build-system]` with `hatchling`. Define:

```toml
[project]
name = "jre-vidget"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer[all]>=0.12",
    "rich>=13",
    "pydantic>=2",
    "yt-dlp>=2024.1.1",
    "ffmpeg-python>=0.2",
]

[project.scripts]
vidget = "jre_vidget.cli:app"

[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "ruff", "mypy"]
```

### 2. Folder structure
Create exactly this layout (empty `__init__.py` files where shown):

```
jre-vidget/
├── pyproject.toml
├── README.md
├── prompts/                  ← already exists, do not touch
├── src/
│   └── jre_vidget/
│       ├── __init__.py
│       ├── cli.py            ← Typer app entry point (stub)
│       ├── engine.py         ← download engine (stub)
│       ├── models.py         ← Pydantic models (stub)
│       ├── config.py         ← config persistence (stub)
│       └── ui.py             ← Rich helpers (stub)
└── tests/
    ├── __init__.py
    └── test_placeholder.py
```

### 3. `src/jre_vidget/cli.py` (stub only)
```python
import typer
from rich.console import Console

app = typer.Typer(
    name="vidget",
    help="🎬  Download & convert videos from 1000+ sites.",
    add_completion=False,
)
console = Console()

@app.command()
def download(url: str = typer.Argument(..., help="Video URL to download")):
    """Download a single video."""
    console.print(f"[bold green]Phase 1 stub:[/] would download {url}")

if __name__ == "__main__":
    app()
```

### 4. `tests/test_placeholder.py`
```python
def test_placeholder():
    assert True
```

### 5. `README.md`
One-paragraph description of the project. List the install command:
```bash
pip install -e ".[dev]"
```
And the planned CLI surface:
```bash
vidget <url>
vidget batch <file>
vidget formats <url>
vidget config show
vidget config set --output ~/Videos --quality 1080p --format mp4
```

---

## Acceptance criteria
- `pip install -e .` completes without errors
- `vidget --help` prints the Typer help panel
- `vidget https://example.com` prints the stub message
- `pytest` passes (1 test, green)
- `ruff check src/` passes with zero warnings
