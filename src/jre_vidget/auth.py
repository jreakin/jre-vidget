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
from pydantic import SecretStr

from jre_vidget.models import AppConfig, AuthConfig

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

_GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"

# Port for OAuth redirect callback (InstalledAppFlow.run_local_server).
OAUTH_LOCAL_SERVER_PORT = 8080


class AuthError(Exception):
    """Raised when credentials are missing, invalid, or cannot be refreshed."""


def login_browser(client_id: str, client_secret: str) -> AuthConfig:
    """
    Run the browser-based OAuth2 flow on localhost (see OAUTH_LOCAL_SERVER_PORT).

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
    creds = flow.run_local_server(port=OAUTH_LOCAL_SERVER_PORT)

    rt = creds.refresh_token
    return AuthConfig(
        client_id=client_id,
        client_secret=SecretStr(client_secret),
        refresh_token=SecretStr(rt) if rt else None,
    )


def get_credentials(auth: AuthConfig) -> Credentials:
    """
    Return valid, refreshed Google credentials.

    Reads client_id, client_secret, and refresh_token from auth, falling back to
    VIDGET_CLIENT_ID, VIDGET_CLIENT_SECRET, and VIDGET_REFRESH_TOKEN environment
    variables (env vars take precedence).

    Raises AuthError if credentials are missing or refresh fails.
    """
    client_id = os.getenv("VIDGET_CLIENT_ID") or auth.client_id
    env_secret = os.getenv("VIDGET_CLIENT_SECRET")
    cfg_secret = auth.client_secret.get_secret_value() if auth.client_secret else None
    client_secret = env_secret or cfg_secret
    env_rt = os.getenv("VIDGET_REFRESH_TOKEN")
    cfg_rt = auth.refresh_token.get_secret_value() if auth.refresh_token else None
    refresh_token = env_rt or cfg_rt

    if not refresh_token or not client_id or not client_secret:
        raise AuthError(
            "Not authenticated. Run 'vidget auth login' to connect your YouTube account."
        )

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
    cfg.save()
    return cfg
