"""
YouTube OAuth credential lifecycle for jre-vidget.

Handles browser-based OAuth login, token refresh, and logout.
No CLI, no Rich, no video logic.

Public API:
  login_browser(client_id, client_secret) -> AuthConfig
  get_credentials(auth) -> google.oauth2.credentials.Credentials
  publish_oauth_configured(auth) -> bool
  logout(cfg) -> AppConfig
"""

from __future__ import annotations

import logging
import os

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from pydantic import SecretStr

from jre_vidget.config import save_app_config
from jre_vidget.models import AppConfig, AuthConfig

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

_GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"

# Default OAuth callback port when ``VIDGET_OAUTH_PORT`` is unset or invalid.
OAUTH_LOCAL_SERVER_PORT = 8080

log = logging.getLogger(__name__)


def _resolve_oauth_local_server_port() -> int:
    """
    Port for :meth:`InstalledAppFlow.run_local_server`.

    Override with ``VIDGET_OAUTH_PORT`` (1–65535). Non-numeric or out-of-range values
    fall back to :data:`OAUTH_LOCAL_SERVER_PORT` and emit a WARNING.
    When the env var is set to a valid port, emit INFO so operators can confirm the value.
    """
    raw = os.getenv("VIDGET_OAUTH_PORT", "").strip()
    if not raw:
        return OAUTH_LOCAL_SERVER_PORT
    try:
        port = int(raw, 10)
    except ValueError:
        log.warning(
            "VIDGET_OAUTH_PORT=%r is not a valid integer; using default port %s",
            raw,
            OAUTH_LOCAL_SERVER_PORT,
        )
        return OAUTH_LOCAL_SERVER_PORT
    if 1 <= port <= 65535:
        log.info("OAuth local callback port %s (from VIDGET_OAUTH_PORT)", port)
        return port
    log.warning(
        "VIDGET_OAUTH_PORT=%r is outside 1–65535; using default port %s",
        raw,
        OAUTH_LOCAL_SERVER_PORT,
    )
    return OAUTH_LOCAL_SERVER_PORT


class AuthError(Exception):
    """Raised when credentials are missing, invalid, or cannot be refreshed."""


def _strip_nonempty(s: str | None) -> str | None:
    if s is None:
        return None
    t = s.strip()
    return t or None


def _field_from_env_chain(names: tuple[str, ...], cfg: str | None) -> str | None:
    """
    First **non-blank** value among defined environment variables, else ``cfg``.

    Used for Google OAuth so newer ``GCLOUD_*`` GitHub secret names take precedence
    over legacy ``VIDGET_*`` names. Blank defined vars are skipped so a later key
    or saved config can supply the value.
    """
    for name in names:
        if name not in os.environ:
            continue
        raw = os.environ.get(name)
        if raw is None:
            continue
        t = raw.strip()
        if t:
            return t
    return _strip_nonempty(cfg)


def _resolved_oauth_triplet(auth: AuthConfig) -> tuple[str, str, str] | None:
    """
    Merge env vars and ``auth`` the same way as :func:`get_credentials`, without refreshing.

    Returns ``None`` if any of client id, client secret, or refresh token is missing/blank.
    """
    client_id = _field_from_env_chain(
        ("GCLOUD_CLIENT_ID", "GCLOUD_AUTH_CLIENT_ID", "VIDGET_CLIENT_ID"),
        auth.client_id,
    )
    cfg_secret = auth.client_secret.get_secret_value() if auth.client_secret else None
    client_secret = _field_from_env_chain(
        ("GCLOUD_CLIENT_SECRET", "VIDGET_CLIENT_SECRET"),
        cfg_secret,
    )
    cfg_rt = auth.refresh_token.get_secret_value() if auth.refresh_token else None
    refresh_token = _field_from_env_chain(
        ("GCLOUD_REFRESH_TOKEN", "VIDGET_REFRESH_TOKEN"),
        cfg_rt,
    )
    if not client_id or not client_secret or not refresh_token:
        return None
    return client_id, client_secret, refresh_token


def publish_oauth_configured(auth: AuthConfig) -> bool:
    """True when OAuth client id, secret, and refresh token are all available (env or config)."""
    return _resolved_oauth_triplet(auth) is not None


def login_browser(client_id: str, client_secret: str) -> AuthConfig:
    """
    Run the browser-based OAuth2 flow on localhost (default port
    :data:`OAUTH_LOCAL_SERVER_PORT`, overridable via ``VIDGET_OAUTH_PORT``).

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
            "token_uri": _GOOGLE_TOKEN_URI,
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=_resolve_oauth_local_server_port())

    rt = creds.refresh_token
    return AuthConfig(
        client_id=client_id,
        client_secret=SecretStr(client_secret),
        refresh_token=SecretStr(rt) if rt else None,
    )


def get_credentials(auth: AuthConfig) -> Credentials:
    """
    Return valid, refreshed Google credentials.

    Reads client_id, client_secret, and refresh_token from auth, merged with
    environment variables. **Client id** (first non-blank wins, in order):
    ``GCLOUD_CLIENT_ID``, ``GCLOUD_AUTH_CLIENT_ID``, ``VIDGET_CLIENT_ID``.
    **Client secret:** ``GCLOUD_CLIENT_SECRET``, ``VIDGET_CLIENT_SECRET``.
    **Refresh token:** ``GCLOUD_REFRESH_TOKEN``, ``VIDGET_REFRESH_TOKEN``.
    Blank defined env values are skipped in favor of later keys or saved config.

    Raises AuthError if credentials are missing or refresh fails.
    """
    triplet = _resolved_oauth_triplet(auth)
    if triplet is None:
        raise AuthError(
            "Not authenticated. Run 'vidget auth login' to connect your YouTube account."
        )
    client_id, client_secret, refresh_token = triplet

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=_GOOGLE_TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )

    # token=None credentials are always invalid (valid=False) but not expired
    # (expired=False), so check refresh_token presence rather than expired flag.
    if not creds.valid and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError as e:
            raise AuthError("YouTube session expired. Run 'vidget auth login' to reconnect.") from e

    return creds


def logout(cfg: AppConfig) -> AppConfig:
    """
    Clear all YouTube credentials from cfg and persist to disk.

    Returns the updated AppConfig.
    """
    cfg.auth = AuthConfig()
    save_app_config(cfg)
    return cfg
