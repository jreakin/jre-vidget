# Phase 8 — YouTube Publish: Auth Module
# Version: 0.1.0
# Model: claude-sonnet-4-6
# Last Updated: 2026-05-03
# Maintainer: jreakin
# Status: Draft

---

## Goal

Implement `auth.py` — the credential lifecycle module for YouTube OAuth. Handles browser
login, token refresh, and logout. No CLI, no Rich, no video logic.

---

## Spec Reference

`docs/superpowers/specs/2026-05-03-youtube-publish-design.md` — `auth.py` section.

---

## Prerequisites

Phase 7 must be complete. `AuthConfig` must be importable from `jre_vidget.models`.

---

## Files

| Action | File |
|--------|------|
| Create | `src/jre_vidget/auth.py` |
| Create | `tests/unit/test_auth.py` |

---

## New Dependencies

Add to `[project.dependencies]` in `pyproject.toml` before starting:

```toml
"google-api-python-client>=2.100",
"google-auth-oauthlib>=1.2",
"google-auth-httplib2>=0.2",
```

Then sync:
```bash
uv sync
```

---

## Implementation

### Step 1 — Write failing tests

Create `tests/unit/test_auth.py`:

```python
"""Tests for auth.py — mocked OAuth flow, no real Google API calls."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jre_vidget.auth import AuthError, get_credentials, login_browser, logout
from jre_vidget.config import load_app_config
from jre_vidget.models import AppConfig, AuthConfig


class TestLoginBrowser:
    def test_returns_auth_config_with_refresh_token(self):
        mock_creds = MagicMock()
        mock_creds.refresh_token = "rt_abc123"
        mock_creds.token = "access_token"

        with patch("jre_vidget.auth.InstalledAppFlow") as mock_flow_cls:
            mock_flow = MagicMock()
            mock_flow.run_local_server.return_value = mock_creds
            mock_flow_cls.from_client_config.return_value = mock_flow

            result = login_browser("my-client-id", "my-client-secret")

        assert result.client_id == "my-client-id"
        assert result.client_secret == "my-client-secret"
        assert result.refresh_token == "rt_abc123"

    def test_flow_called_with_correct_scope(self):
        mock_creds = MagicMock()
        mock_creds.refresh_token = "rt"

        with patch("jre_vidget.auth.InstalledAppFlow") as mock_flow_cls:
            mock_flow = MagicMock()
            mock_flow.run_local_server.return_value = mock_creds
            mock_flow_cls.from_client_config.return_value = mock_flow

            login_browser("cid", "csecret")

        call_kwargs = mock_flow_cls.from_client_config.call_args
        scopes = call_kwargs[0][1]  # second positional arg is scopes list
        assert "https://www.googleapis.com/auth/youtube.upload" in scopes

    def test_run_local_server_on_port_8080(self):
        mock_creds = MagicMock()
        mock_creds.refresh_token = "rt"

        with patch("jre_vidget.auth.InstalledAppFlow") as mock_flow_cls:
            mock_flow = MagicMock()
            mock_flow.run_local_server.return_value = mock_creds
            mock_flow_cls.from_client_config.return_value = mock_flow

            login_browser("cid", "csecret")

        mock_flow.run_local_server.assert_called_once_with(port=8080)


class TestGetCredentials:
    def test_returns_credentials_when_configured(self):
        auth = AuthConfig(
            client_id="cid",
            client_secret="csecret",
            refresh_token="rt",
        )
        mock_creds = MagicMock()
        mock_creds.valid = True

        with patch("jre_vidget.auth.Credentials") as mock_creds_cls:
            mock_creds_cls.return_value = mock_creds
            creds = get_credentials(auth)

        assert creds is mock_creds

    def test_raises_auth_error_when_no_refresh_token(self):
        auth = AuthConfig(client_id="cid", client_secret="csecret")
        with pytest.raises(AuthError, match="Run 'vidget auth login'"):
            get_credentials(auth)

    def test_raises_auth_error_when_no_credentials_at_all(self):
        auth = AuthConfig()
        with pytest.raises(AuthError, match="Run 'vidget auth login'"):
            get_credentials(auth)

    def test_refreshes_expired_token(self):
        auth = AuthConfig(client_id="cid", client_secret="csecret", refresh_token="rt")
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "rt"

        with patch("jre_vidget.auth.Credentials") as mock_creds_cls:
            with patch("jre_vidget.auth.Request") as mock_request_cls:
                mock_creds_cls.return_value = mock_creds
                get_credentials(auth)

        mock_creds.refresh.assert_called_once()

    def test_raises_auth_error_on_refresh_failure(self):
        from google.auth.exceptions import RefreshError

        auth = AuthConfig(client_id="cid", client_secret="csecret", refresh_token="rt")
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh.side_effect = RefreshError("token revoked")

        with patch("jre_vidget.auth.Credentials") as mock_creds_cls:
            with patch("jre_vidget.auth.Request"):
                mock_creds_cls.return_value = mock_creds
                with pytest.raises(AuthError, match="session expired"):
                    get_credentials(auth)

    def test_env_vars_override_config(self, monkeypatch):
        """VIDGET_CLIENT_ID / VIDGET_CLIENT_SECRET take precedence over AuthConfig."""
        monkeypatch.setenv("VIDGET_CLIENT_ID", "env-client-id")
        monkeypatch.setenv("VIDGET_CLIENT_SECRET", "env-client-secret")

        # AuthConfig has different (or missing) client_id/secret
        auth = AuthConfig(client_id="config-id", client_secret="config-secret", refresh_token="rt")
        mock_creds = MagicMock()
        mock_creds.valid = True

        with patch("jre_vidget.auth.Credentials") as mock_creds_cls:
            mock_creds_cls.return_value = mock_creds
            get_credentials(auth)

        _, kwargs = mock_creds_cls.call_args
        assert kwargs["client_id"] == "env-client-id"
        assert kwargs["client_secret"] == "env-client-secret"


class TestLogout:
    def test_clears_all_auth_fields(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        cfg = AppConfig()
        cfg.auth = AuthConfig(
            client_id="cid",
            client_secret="csecret",
            refresh_token="rt",
        )

        result = logout(cfg)

        assert result.auth.client_id is None
        assert result.auth.client_secret is None
        assert result.auth.refresh_token is None

    def test_saves_to_disk(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg
        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token="rt")
        result = logout(cfg)

        restored = load_app_config()
        assert restored.auth.refresh_token is None
```

Run — confirm all fail:
```bash
uv run pytest tests/unit/test_auth.py -v
```
Expected: `ModuleNotFoundError: No module named 'jre_vidget.auth'`

---

### Step 2 — Implement `auth.py`

Create `src/jre_vidget/auth.py`:

```python
"""
YouTube OAuth credential lifecycle for jre-vidget.

Handles browser-based OAuth login, token refresh, and logout.
No CLI, no Rich, no video logic.

Public API:
  login_browser(client_id, client_secret) -> AuthConfig
  get_credentials(auth) -> google.oauth2.credentials.Credentials
  logout(cfg) -> AppConfig
"""

from __future__ import annotations

import os

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from jre_vidget.config import save_app_config
from jre_vidget.models import AppConfig, AuthConfig

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class AuthError(Exception):
    """Raised when credentials are missing, invalid, or cannot be refreshed."""


def login_browser(client_id: str, client_secret: str) -> AuthConfig:
    """
    Run the browser-based OAuth2 flow on localhost:8080.

    Opens the Google consent URL in the user's default browser, waits for the
    redirect callback, and returns an AuthConfig with refresh_token populated.

    The caller is responsible for persisting the result to AppConfig.
    """
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=8080)

    return AuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=creds.refresh_token,
    )


def get_credentials(auth: AuthConfig) -> Credentials:
    """
    Return valid, refreshed Google credentials.

    Reads client_id and client_secret from auth, falling back to
    VIDGET_CLIENT_ID / VIDGET_CLIENT_SECRET environment variables.

    Raises AuthError if credentials are missing or refresh fails.
    """
    client_id = os.getenv("VIDGET_CLIENT_ID") or auth.client_id
    client_secret = os.getenv("VIDGET_CLIENT_SECRET") or auth.client_secret

    if not auth.refresh_token or not client_id or not client_secret:
        raise AuthError(
            "Not authenticated. Run 'vidget auth login' to connect your YouTube account."
        )

    creds = Credentials(
        token=None,
        refresh_token=auth.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )

    # token=None credentials are always invalid (valid=False) but not expired
    # (expired=False), so check refresh_token presence rather than expired flag.
    if not creds.valid:
        if creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError as e:
                raise AuthError(
                    "YouTube session expired. Run 'vidget auth login' to reconnect."
                ) from e

    return creds


def logout(cfg: AppConfig) -> AppConfig:
    """
    Clear all YouTube credentials from cfg and persist to disk.

    Returns the updated AppConfig.
    """
    cfg.auth = AuthConfig()
    save_app_config(cfg)
    return cfg
```

---

### Step 3 — Run tests

```bash
uv run pytest tests/unit/test_auth.py -v
```
Expected: all tests **PASS**.

Also confirm no regressions:
```bash
uv run pytest tests/unit/ -v
```

---

### Step 4 — Type check and lint

```bash
uv run mypy src/jre_vidget/auth.py --strict
uv run ruff check src/jre_vidget/auth.py
```
Expected: no errors.

---

### Step 5 — Commit

```bash
git add src/jre_vidget/auth.py tests/unit/test_auth.py pyproject.toml
git commit -m "feat: add YouTube OAuth auth module"
```

---

## Acceptance Criteria

- [ ] `auth.py` exports `AuthError`, `login_browser`, `get_credentials`, `logout`
- [ ] `login_browser` uses `InstalledAppFlow` on port 8080 with `youtube.upload` scope
- [ ] `get_credentials` raises `AuthError` when `refresh_token` is missing
- [ ] `get_credentials` refreshes expired tokens transparently
- [ ] `get_credentials` raises `AuthError` on `RefreshError`
- [ ] `get_credentials` reads `VIDGET_CLIENT_ID` / `VIDGET_CLIENT_SECRET` env vars
- [ ] `logout` clears all fields and calls `save_app_config(cfg)`
- [ ] All tests in `test_auth.py` pass
- [ ] No existing tests broken
- [ ] `mypy --strict` clean
