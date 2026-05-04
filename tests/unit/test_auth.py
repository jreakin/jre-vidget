"""Tests for auth.py — mocked OAuth flow, no real Google API calls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from jre_vidget.auth import AuthError, get_credentials, login_browser, logout
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
        assert result.client_secret is not None
        assert result.client_secret.get_secret_value() == "my-client-secret"
        assert result.refresh_token is not None
        assert result.refresh_token.get_secret_value() == "rt_abc123"

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
            client_secret=SecretStr("csecret"),
            refresh_token=SecretStr("rt"),
        )
        mock_creds = MagicMock()
        mock_creds.valid = True

        with patch("jre_vidget.auth.Credentials") as mock_creds_cls:
            mock_creds_cls.return_value = mock_creds
            creds = get_credentials(auth)

        assert creds is mock_creds

    def test_raises_auth_error_when_no_refresh_token(self):
        auth = AuthConfig(client_id="cid", client_secret=SecretStr("csecret"))
        with pytest.raises(AuthError, match="Run 'vidget auth login'"):
            get_credentials(auth)

    def test_raises_auth_error_when_no_credentials_at_all(self):
        auth = AuthConfig()
        with pytest.raises(AuthError, match="Run 'vidget auth login'"):
            get_credentials(auth)

    def test_refreshes_expired_token(self):
        auth = AuthConfig(
            client_id="cid",
            client_secret=SecretStr("csecret"),
            refresh_token=SecretStr("rt"),
        )
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "rt"

        with (
            patch("jre_vidget.auth.Credentials") as mock_creds_cls,
            patch("jre_vidget.auth.Request"),
        ):
            mock_creds_cls.return_value = mock_creds
            get_credentials(auth)

        mock_creds.refresh.assert_called_once()

    def test_raises_auth_error_on_refresh_failure(self):
        from google.auth.exceptions import RefreshError

        auth = AuthConfig(
            client_id="cid",
            client_secret=SecretStr("csecret"),
            refresh_token=SecretStr("rt"),
        )
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh.side_effect = RefreshError("token revoked")

        with (
            patch("jre_vidget.auth.Credentials") as mock_creds_cls,
            patch("jre_vidget.auth.Request"),
        ):
            mock_creds_cls.return_value = mock_creds
            with pytest.raises(AuthError, match="session expired"):
                get_credentials(auth)

    def test_env_vars_override_config(self, monkeypatch):
        """VIDGET_CLIENT_ID / VIDGET_CLIENT_SECRET take precedence over AuthConfig."""
        monkeypatch.setenv("VIDGET_CLIENT_ID", "env-client-id")
        monkeypatch.setenv("VIDGET_CLIENT_SECRET", "env-client-secret")

        # AuthConfig has different (or missing) client_id/secret
        auth = AuthConfig(
            client_id="config-id",
            client_secret=SecretStr("config-secret"),
            refresh_token=SecretStr("rt"),
        )
        mock_creds = MagicMock()
        mock_creds.valid = True

        with patch("jre_vidget.auth.Credentials") as mock_creds_cls:
            mock_creds_cls.return_value = mock_creds
            get_credentials(auth)

        _, kwargs = mock_creds_cls.call_args
        assert kwargs["client_id"] == "env-client-id"
        assert kwargs["client_secret"] == "env-client-secret"

    def test_env_var_refresh_token_overrides_config(self, monkeypatch):
        """VIDGET_REFRESH_TOKEN env var takes precedence over AuthConfig.refresh_token."""
        monkeypatch.setenv("VIDGET_REFRESH_TOKEN", "env-refresh-token")
        auth = AuthConfig(
            client_id="cid",
            client_secret=SecretStr("csecret"),
            refresh_token=SecretStr("config-token"),
        )
        mock_creds = MagicMock()
        mock_creds.valid = True

        with patch("jre_vidget.auth.Credentials") as mock_creds_cls:
            mock_creds_cls.return_value = mock_creds
            get_credentials(auth)

        _, kwargs = mock_creds_cls.call_args
        assert kwargs["refresh_token"] == "env-refresh-token"

    def test_env_var_refresh_token_allows_empty_config(self, monkeypatch):
        """All three env vars set → AuthConfig can be completely empty."""
        monkeypatch.setenv("VIDGET_REFRESH_TOKEN", "env-rt")
        monkeypatch.setenv("VIDGET_CLIENT_ID", "env-cid")
        monkeypatch.setenv("VIDGET_CLIENT_SECRET", "env-csecret")

        mock_creds = MagicMock()
        mock_creds.valid = True

        with patch("jre_vidget.auth.Credentials") as mock_creds_cls:
            mock_creds_cls.return_value = mock_creds
            get_credentials(AuthConfig())  # no config values at all — should not raise

        _, kwargs = mock_creds_cls.call_args
        assert kwargs["refresh_token"] == "env-rt"
        assert kwargs["client_id"] == "env-cid"
        assert kwargs["client_secret"] == "env-csecret"


class TestLogout:
    def test_clears_all_auth_fields(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg

        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        cfg = AppConfig()
        cfg.auth = AuthConfig(
            client_id="cid",
            client_secret=SecretStr("csecret"),
            refresh_token=SecretStr("rt"),
        )

        result = logout(cfg)

        assert result.auth.client_id is None
        assert result.auth.client_secret is None
        assert result.auth.refresh_token is None

    def test_saves_to_disk(self, tmp_path, monkeypatch):
        import jre_vidget.config as vidget_cfg

        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token=SecretStr("rt"))
        logout(cfg)

        restored = AppConfig.load()
        assert restored.auth.refresh_token is None
