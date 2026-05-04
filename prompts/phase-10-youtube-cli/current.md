# Phase 10 — YouTube Publish: CLI Integration
# Version: 0.1.0
# Model: claude-sonnet-4-6
# Last Updated: 2026-05-03
# Maintainer: jreakin
# Status: Draft

---

## Goal

Wire `auth.py` and `publisher.py` into the Typer CLI. Add the `auth` subcommand group
(`login`, `status`, `logout`), the `publish` command, and a `--publish` flag on the
existing `download` command.

---

## Spec Reference

`docs/superpowers/specs/2026-05-03-youtube-publish-design.md` — CLI Commands section.

---

## Prerequisites

- Phase 7 complete (`AuthConfig`, `PublishConfig`, `PublishResult`)
- Phase 8 complete (`auth.py`)
- Phase 9 complete (`publisher.py`)

---

## Files

| Action | File |
|--------|------|
| Modify | `src/jre_vidget/cli.py` |
| Create | `tests/integration/test_youtube_cli.py` |

---

## Context: Current `cli.py` Structure

`cli.py` uses a main `app = typer.Typer(name="vidget")` with subcommand groups for
existing commands. The `download` command already exists. Follow the same patterns:
- Commands use `typer.Option()` for flags
- Rich output via `console = Console()` from `ui.py`
- Errors print via `console.print(...)` then `raise typer.Exit(code)`
- `load_app_config()` called at the start of commands that need user config

---

## Implementation

### Step 1 — Write failing integration tests

Create `tests/integration/test_youtube_cli.py`:

```python
"""Integration tests for YouTube CLI commands — mocked auth and publisher."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from jre_vidget.cli import app
from jre_vidget.config import load_app_config, save_app_config
from jre_vidget.models import AppConfig, AuthConfig, PublishResult

runner = CliRunner()


# ---------------------------------------------------------------------------
# auth login
# ---------------------------------------------------------------------------
class TestAuthLogin:
    def test_login_prompts_for_credentials(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        mock_auth_config = AuthConfig(
            client_id="cid",
            client_secret="csecret",
            refresh_token="rt",
        )
        with patch("jre_vidget.cli.auth.login_browser", return_value=mock_auth_config):
            result = runner.invoke(
                app,
                ["auth", "login"],
                input="my-client-id\nmy-client-secret\n",
            )

        assert result.exit_code == 0
        assert "connected" in result.output.lower() or "success" in result.output.lower()

    def test_login_saves_credentials(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        mock_auth_config = AuthConfig(
            client_id="cid",
            client_secret="csecret",
            refresh_token="saved_token",
        )
        with patch("jre_vidget.cli.auth.login_browser", return_value=mock_auth_config):
            runner.invoke(
                app,
                ["auth", "login"],
                input="cid\ncsecret\n",
            )

        cfg = load_app_config()
        assert cfg.auth.refresh_token == "saved_token"


# ---------------------------------------------------------------------------
# auth status
# ---------------------------------------------------------------------------
class TestAuthStatus:
    def test_shows_connected_when_token_present(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token="rt")
        save_app_config(cfg)

        result = runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        assert "connected" in result.output.lower()

    def test_shows_not_connected_when_no_token(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        result = runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        assert "not connected" in result.output.lower() or "login" in result.output.lower()


# ---------------------------------------------------------------------------
# auth logout
# ---------------------------------------------------------------------------
class TestAuthLogout:
    def test_logout_clears_token(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token="rt")
        save_app_config(cfg)

        result = runner.invoke(app, ["auth", "logout"])
        assert result.exit_code == 0

        restored = load_app_config()
        assert restored.auth.refresh_token is None


# ---------------------------------------------------------------------------
# vidget publish
# ---------------------------------------------------------------------------
class TestPublishCommand:
    def test_publish_success(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token="rt")
        save_app_config(cfg)

        mock_result = PublishResult(
            video_id="abc123",
            url="https://youtube.com/watch?v=abc123",
            title="video",
            privacy="public",
        )
        with patch("jre_vidget.cli.publisher.upload", return_value=mock_result):
            result = runner.invoke(app, ["publish", str(video)])

        assert result.exit_code == 0
        assert "abc123" in result.output

    def test_publish_with_custom_title(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token="rt")
        save_app_config(cfg)

        with patch("jre_vidget.cli.publisher.upload") as mock_upload:
            mock_upload.return_value = PublishResult(
                video_id="x", url="https://youtube.com/watch?v=x",
                title="Custom", privacy="public"
            )
            runner.invoke(app, ["publish", str(video), "--title", "Custom Title"])

        publish_config = mock_upload.call_args[0][0]
        assert publish_config.title == "Custom Title"

    def test_publish_exits_3_when_not_authenticated(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")

        from jre_vidget.auth import AuthError
        with patch("jre_vidget.cli.publisher.upload", side_effect=AuthError("not authed")):
            result = runner.invoke(app, ["publish", str(video)])

        assert result.exit_code == 3

    def test_publish_exits_1_on_publish_error(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token="rt")
        save_app_config(cfg)

        from jre_vidget.publisher import PublishError
        with patch("jre_vidget.cli.publisher.upload", side_effect=PublishError("bad")):
            result = runner.invoke(app, ["publish", str(video)])

        assert result.exit_code == 1

    def test_publish_privacy_flag(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token="rt")
        save_app_config(cfg)

        with patch("jre_vidget.cli.publisher.upload") as mock_upload:
            mock_upload.return_value = PublishResult(
                video_id="x", url="https://youtube.com/watch?v=x",
                title="t", privacy="private"
            )
            runner.invoke(app, ["publish", str(video), "--privacy", "private"])

        publish_config = mock_upload.call_args[0][0]
        assert publish_config.privacy == "private"


# ---------------------------------------------------------------------------
# download --publish flag
# ---------------------------------------------------------------------------
class TestDownloadWithPublish:
    def test_download_publish_calls_fetch_info_first(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        from jre_vidget.models import (
            AppConfig, DownloadResult, DownloadStatus, VideoInfo,
        )
        from datetime import datetime

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token="rt")
        save_app_config(cfg)

        fake_file = tmp_path / "video.mp4"
        fake_file.touch()

        mock_info = MagicMock(spec=VideoInfo)
        mock_info.title = "Scraped Title"

        mock_dl_result = DownloadResult(
            url="https://example.com",
            status=DownloadStatus.SUCCESS,
            filepath=fake_file,
            finished_at=datetime.now(),
        )
        mock_pub_result = PublishResult(
            video_id="xyz",
            url="https://youtube.com/watch?v=xyz",
            title="Scraped Title",
            privacy="public",
        )

        with patch("jre_vidget.cli.engine.fetch_info", return_value=mock_info) as mock_fi:
            with patch("jre_vidget.cli.engine.download", return_value=mock_dl_result):
                with patch("jre_vidget.cli.publisher.upload", return_value=mock_pub_result):
                    result = runner.invoke(
                        app,
                        ["download", "https://example.com", "--publish",
                         "--output", str(tmp_path)],
                    )

        mock_fi.assert_called_once_with("https://example.com")
        assert result.exit_code == 0
        assert "xyz" in result.output

    def test_download_publish_uses_scraped_title(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        from jre_vidget.models import (
            AppConfig, DownloadResult, DownloadStatus, VideoInfo,
        )
        from datetime import datetime

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token="rt")
        save_app_config(cfg)

        fake_file = tmp_path / "video.mp4"
        fake_file.touch()

        mock_info = MagicMock(spec=VideoInfo)
        mock_info.title = "Fox News Segment"

        mock_dl_result = DownloadResult(
            url="https://example.com",
            status=DownloadStatus.SUCCESS,
            filepath=fake_file,
            finished_at=datetime.now(),
        )

        with patch("jre_vidget.cli.engine.fetch_info", return_value=mock_info):
            with patch("jre_vidget.cli.engine.download", return_value=mock_dl_result):
                with patch("jre_vidget.cli.publisher.upload") as mock_pub:
                    mock_pub.return_value = PublishResult(
                        video_id="x", url="https://youtube.com/watch?v=x",
                        title="Fox News Segment", privacy="public"
                    )
                    runner.invoke(
                        app,
                        ["download", "https://example.com", "--publish",
                         "--output", str(tmp_path)],
                    )

        publish_config = mock_pub.call_args[0][0]
        assert publish_config.title == "Fox News Segment"

    def test_download_publish_title_override(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        from jre_vidget.models import (
            AppConfig, DownloadResult, DownloadStatus,
        )
        from datetime import datetime

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token="rt")
        save_app_config(cfg)

        fake_file = tmp_path / "video.mp4"
        fake_file.touch()

        mock_info = MagicMock()
        mock_info.title = "Original Title"

        mock_dl_result = DownloadResult(
            url="https://example.com",
            status=DownloadStatus.SUCCESS,
            filepath=fake_file,
            finished_at=datetime.now(),
        )

        with patch("jre_vidget.cli.engine.fetch_info", return_value=mock_info):
            with patch("jre_vidget.cli.engine.download", return_value=mock_dl_result):
                with patch("jre_vidget.cli.publisher.upload") as mock_pub:
                    mock_pub.return_value = PublishResult(
                        video_id="x", url="https://youtube.com/watch?v=x",
                        title="My Override", privacy="public"
                    )
                    runner.invoke(
                        app,
                        ["download", "https://example.com", "--publish",
                         "--title", "My Override", "--output", str(tmp_path)],
                    )

        publish_config = mock_pub.call_args[0][0]
        assert publish_config.title == "My Override"

    def test_download_without_publish_does_not_call_publisher(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        from jre_vidget.models import DownloadResult, DownloadStatus
        from datetime import datetime

        fake_file = tmp_path / "video.mp4"
        fake_file.touch()

        mock_dl_result = DownloadResult(
            url="https://example.com",
            status=DownloadStatus.SUCCESS,
            filepath=fake_file,
            finished_at=datetime.now(),
        )

        with patch("jre_vidget.cli.engine.download", return_value=mock_dl_result):
            with patch("jre_vidget.cli.publisher.upload") as mock_pub:
                runner.invoke(
                    app,
                    ["download", "https://example.com", "--output", str(tmp_path)],
                )

        mock_pub.assert_not_called()
```

Run — confirm all fail:
```bash
uv run pytest tests/integration/test_youtube_cli.py -v
```
Expected: failures because `auth` subcommand, `publish` command, and `--publish` flag
don't exist yet.

---

### Step 2 — Add imports to `cli.py`

Locate the existing module-level import line:
```python
from jre_vidget import checks, engine, models, ui
```
Extend it to include `auth` and `publisher`:
```python
from jre_vidget import auth, checks, engine, models, publisher, ui
```

Also add these named imports and a module-level console below the existing imports:
```python
from jre_vidget.auth import AuthError
from jre_vidget.publisher import PublishError
from jre_vidget.models import PublishConfig
from rich.console import Console

console = Console()
```

---

### Step 3 — Add `auth` subcommand group to `cli.py`

```python
from jre_vidget.config import load_app_config, save_app_config

auth_app = typer.Typer(name="auth", help="Manage YouTube account connection.")
app.add_typer(auth_app)


@auth_app.command("login")
def auth_login() -> None:
    """Connect your YouTube account via browser OAuth."""
    cfg = load_app_config()

    # Reuse stored credentials if already present
    client_id = cfg.auth.client_id or typer.prompt("Google OAuth Client ID")
    client_secret = cfg.auth.client_secret or typer.prompt(
        "Google OAuth Client Secret", hide_input=True
    )

    try:
        auth_config = auth.login_browser(client_id, client_secret)
    except Exception as e:
        console.print(f"[red]Login failed:[/red] {e}")
        raise typer.Exit(1)

    cfg.auth = auth_config
    save_app_config(cfg)
    console.print("[green]✓[/green] YouTube connected successfully.")


@auth_app.command("status")
def auth_status() -> None:
    """Show YouTube connection status."""
    cfg = load_app_config()
    if cfg.auth.refresh_token:
        console.print("[green]✓[/green] YouTube  connected")
    else:
        console.print("[yellow]✗[/yellow] YouTube  not connected — run [bold]vidget auth login[/bold]")


@auth_app.command("logout")
def auth_logout() -> None:
    """Disconnect your YouTube account."""
    cfg = load_app_config()
    auth.logout(cfg)
    console.print("[green]✓[/green] YouTube disconnected.")
```

---

### Step 4 — Add `publish` command to `cli.py`

```python
from jre_vidget.config import load_app_config

@app.command()
def publish(
    filepath: Path = typer.Argument(..., help="Path to the local video file to upload."),
    title: str | None = typer.Option(None, "--title", help="Video title (default: filename)."),
    description: str = typer.Option("", "--description", help="Video description."),
    privacy: str = typer.Option("public", "--privacy", help="public | unlisted | private"),
    remove: bool = typer.Option(False, "--remove", help="Delete local file after successful upload."),
) -> None:
    """Upload a local video file to your YouTube channel."""
    cfg = load_app_config()

    if not filepath.exists():
        console.print(f"[red]File not found:[/red] {filepath}")
        raise typer.Exit(1)

    resolved_title = title or filepath.stem

    publish_config = PublishConfig(
        filepath=filepath,
        title=resolved_title,
        description=description,
        privacy=privacy,
        remove_after_upload=remove,
    )

    try:
        with console.status("Uploading to YouTube…"):
            result = publisher.upload(publish_config, cfg.auth)
    except AuthError as e:
        console.print(f"[red]Auth error:[/red] {e}")
        raise typer.Exit(3)
    except PublishError as e:
        console.print(f"[red]Upload failed:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Published: {result.url}")
    if result.removed_local_file:
        console.print(f"  Local file removed: {filepath}")
```

---

### Step 5 — Add `--publish` flag to the existing `download` command

Locate the existing `download` command in `cli.py`. Add these parameters to its
signature and add the publish block at the end of the function body:

```python
# Add to download() signature:
publish_flag: bool = typer.Option(False, "--publish", help="Upload to YouTube after download."),
pub_title: str | None = typer.Option(None, "--title", help="YouTube title (default: scraped title)."),
pub_description: str = typer.Option("", "--description", help="YouTube description."),
pub_privacy: str = typer.Option("public", "--privacy", help="public | unlisted | private"),
pub_remove: bool = typer.Option(False, "--remove", help="Delete local file after upload."),
```

```python
# Add at the end of the download() function body, after a successful download:
# (ensure ``from jre_vidget.config import load_app_config`` at module scope)
if publish_flag and result.status == DownloadStatus.SUCCESS and result.filepath:
    cfg = load_app_config()
    # fetch_info was called before download — use scraped title or fall back to URL
    resolved_title = pub_title or (video_info.title if video_info else url)

    publish_config = PublishConfig(
        filepath=result.filepath,
        title=resolved_title,
        description=pub_description,
        privacy=pub_privacy,
        remove_after_upload=pub_remove,
    )

    try:
        with console.status("Uploading to YouTube…"):
            pub_result = publisher.upload(publish_config, cfg.auth)
    except AuthError as e:
        console.print(f"[red]YouTube auth error:[/red] {e}")
        raise typer.Exit(3)
    except PublishError as e:
        console.print(f"[red]YouTube upload failed:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Published: {pub_result.url}")
```

**Important:** The `download` command must call `engine.fetch_info(url)` before
`engine.download(config)` when `--publish` is set, to obtain `video_info.title`.
Add this block at the start of the download command body when `publish_flag` is True:

```python
video_info = None
if publish_flag:
    try:
        video_info = engine.fetch_info(url)
    except engine.EngineError as e:
        console.print(f"[yellow]Warning:[/yellow] Could not fetch video info: {e}")
        video_info = None
```

If `video_info` is `None` (fetch failed), fall back to the URL as the title.

---

### Step 6 — Run tests

```bash
uv run pytest tests/integration/test_youtube_cli.py -v
```
Expected: all tests **PASS**.

Run full suite:
```bash
uv run pytest -v
```
Expected: all tests pass with no regressions.

---

### Step 7 — Type check and lint

```bash
uv run mypy src/jre_vidget/cli.py --strict
uv run ruff check src/jre_vidget/cli.py
uv run ruff format src/jre_vidget/cli.py
```
Expected: no errors.

---

### Step 8 — Manual smoke test (optional but recommended)

```bash
uv run vidget auth --help
uv run vidget auth login --help
uv run vidget publish --help
uv run vidget download --help   # should show --publish, --title, --privacy, --remove
```

---

### Step 9 — Commit

```bash
git add src/jre_vidget/cli.py tests/integration/test_youtube_cli.py
git commit -m "feat: add YouTube auth commands, publish command, and --publish flag on download"
```

---

## Acceptance Criteria

- [ ] `vidget auth login` prompts for client ID/secret, opens browser, saves token
- [ ] `vidget auth status` shows connected/not connected
- [ ] `vidget auth logout` clears stored credentials
- [ ] `vidget publish FILE` uploads with public privacy by default
- [ ] `vidget publish FILE --title --description --privacy --remove` all work
- [ ] `vidget publish` exits 3 on `AuthError`, exits 1 on `PublishError`
- [ ] `vidget download URL --publish` calls `fetch_info` before download
- [ ] `vidget download URL --publish` uses scraped title by default
- [ ] `vidget download URL --publish --title X` uses override title
- [ ] `vidget download URL` (no `--publish`) never calls `publisher.upload`
- [ ] `--remove` applies only to the upload step, not the download step
- [ ] All integration tests in `test_youtube_cli.py` pass
- [ ] Full test suite passes with no regressions
- [ ] `mypy --strict` clean on `cli.py`
