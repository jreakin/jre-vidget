"""OAuth env + config merge for publish / ``get_credentials`` (no network)."""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from jre_vidget.auth import _resolved_oauth_triplet, publish_oauth_configured
from jre_vidget.models import AuthConfig


def test_triplet_prefers_nonblank_env_over_config(monkeypatch: pytest.MonkeyPatch) -> None:
    auth = AuthConfig(
        client_id="cfg-id",
        client_secret=SecretStr("cfg-sec"),
        refresh_token=SecretStr("cfg-rt"),
    )
    monkeypatch.setenv("VIDGET_CLIENT_ID", "env-id")
    monkeypatch.setenv("VIDGET_CLIENT_SECRET", "env-secret")
    monkeypatch.setenv("VIDGET_REFRESH_TOKEN", "env-rt")
    t = _resolved_oauth_triplet(auth)
    assert t == ("env-id", "env-secret", "env-rt")


def test_triplet_blank_env_refresh_falls_back_to_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Whitespace-only env must not block using the saved refresh token."""
    auth = AuthConfig(
        client_id="a",
        client_secret=SecretStr("b"),
        refresh_token=SecretStr("from-file"),
    )
    monkeypatch.setenv("VIDGET_REFRESH_TOKEN", "   ")
    t = _resolved_oauth_triplet(auth)
    assert t == ("a", "b", "from-file")


def test_triplet_empty_string_env_falls_back_to_config(monkeypatch: pytest.MonkeyPatch) -> None:
    auth = AuthConfig(
        client_id="cid",
        client_secret=SecretStr("csec"),
        refresh_token=SecretStr("crt"),
    )
    monkeypatch.setenv("VIDGET_CLIENT_ID", "")
    monkeypatch.setenv("VIDGET_CLIENT_SECRET", "")
    monkeypatch.setenv("VIDGET_REFRESH_TOKEN", "")
    t = _resolved_oauth_triplet(auth)
    assert t == ("cid", "csec", "crt")


def test_triplet_none_when_any_field_missing() -> None:
    auth = AuthConfig(
        client_id="x",
        client_secret=SecretStr("y"),
        refresh_token=None,
    )
    assert _resolved_oauth_triplet(auth) is None


def test_publish_oauth_configured_matches_triplet() -> None:
    assert not publish_oauth_configured(AuthConfig())
    assert publish_oauth_configured(
        AuthConfig(
            client_id="i",
            client_secret=SecretStr("s"),
            refresh_token=SecretStr("r"),
        ),
    )
