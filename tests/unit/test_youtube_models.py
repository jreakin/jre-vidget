"""Tests for YouTube publish models."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from jre_vidget.models import (
    AppConfig,
    AuthConfig,
    PrivacyStatus,
    PublishConfig,
    PublishResult,
)


class TestAuthConfig:
    def test_defaults(self) -> None:
        cfg = AuthConfig()
        assert cfg.client_id is None
        assert cfg.client_secret is None
        assert cfg.refresh_token is None

    def test_loads_plaintext_secrets_from_json(self) -> None:
        """Disk / API JSON uses plain strings; ``model_dump_json`` masks secrets."""
        raw = '{"client_id":"cid","client_secret":"csecret","refresh_token":"rtoken"}'
        restored = AuthConfig.model_validate_json(raw)
        assert restored.client_id == "cid"
        assert restored.client_secret is not None
        assert restored.client_secret.get_secret_value() == "csecret"
        assert restored.refresh_token is not None
        assert restored.refresh_token.get_secret_value() == "rtoken"

    def test_partial_population(self) -> None:
        cfg = AuthConfig(client_id="only-id")
        assert cfg.client_secret is None
        assert cfg.refresh_token is None


class TestPublishConfig:
    def test_required_fields(self, tmp_path: Path) -> None:
        filepath = tmp_path / "video.mp4"
        filepath.touch()
        cfg = PublishConfig(filepath=filepath, title="My Video")
        assert cfg.title == "My Video"
        assert cfg.privacy == "public"
        assert cfg.remove_after_upload is False
        assert cfg.description == ""

    def test_title_is_required(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError):
            PublishConfig.model_validate({"filepath": tmp_path / "video.mp4"})

    def test_privacy_options(self, tmp_path: Path) -> None:
        filepath = tmp_path / "video.mp4"
        filepath.touch()
        for privacy in PrivacyStatus:
            cfg = PublishConfig(filepath=filepath, title="t", privacy=privacy)
            assert cfg.privacy == privacy

    def test_invalid_privacy_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError):
            PublishConfig.model_validate(
                {
                    "filepath": tmp_path / "video.mp4",
                    "title": "t",
                    "privacy": "secret",
                }
            )

    def test_privacy_json_roundtrip(self, tmp_path: Path) -> None:
        filepath = tmp_path / "video.mp4"
        filepath.touch()
        cfg = PublishConfig(filepath=filepath, title="t", privacy=PrivacyStatus.UNLISTED)
        dumped = cfg.model_dump(mode="json")
        assert dumped["privacy"] == "unlisted"
        restored = PublishConfig.model_validate(dumped)
        assert restored.privacy == PrivacyStatus.UNLISTED

    def test_remove_after_upload_flag(self, tmp_path: Path) -> None:
        cfg = PublishConfig(
            filepath=tmp_path / "video.mp4",
            title="t",
            remove_after_upload=True,
        )
        assert cfg.remove_after_upload is True


class TestPublishResult:
    def test_url_construction(self) -> None:
        result = PublishResult(
            video_id="abc123",
            url="https://youtube.com/watch?v=abc123",
            title="My Video",
            privacy=PrivacyStatus.PUBLIC,
        )
        assert "abc123" in result.url
        assert result.removed_local_file is False

    def test_removed_local_file_flag(self) -> None:
        result = PublishResult(
            video_id="x",
            url="https://youtube.com/watch?v=x",
            title="t",
            privacy=PrivacyStatus.PUBLIC,
            removed_local_file=True,
        )
        assert result.removed_local_file is True


class TestAppConfigEmbedding:
    def test_app_config_has_auth(self) -> None:
        cfg = AppConfig()
        assert hasattr(cfg, "auth")
        assert isinstance(cfg.auth, AuthConfig)
        assert cfg.auth.refresh_token is None

    def test_app_config_persists_auth(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import jre_vidget.config as vidget_cfg

        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token=SecretStr("mytoken"))
        cfg.save()

        restored = AppConfig.load()
        assert restored.auth.refresh_token is not None
        assert restored.auth.refresh_token.get_secret_value() == "mytoken"

    def test_app_config_save_writes_plaintext_oauth_to_disk(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import jre_vidget.config as vidget_cfg

        monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")

        cfg = AppConfig()
        cfg.auth = AuthConfig(
            client_id="id1",
            client_secret=SecretStr("plain-secret"),
            refresh_token=SecretStr("plain-rt"),
        )
        cfg.save()

        raw = (tmp_path / "config.json").read_text(encoding="utf-8")
        assert "plain-secret" in raw
        assert "plain-rt" in raw
        assert "**********" not in raw

        restored = AppConfig.load()
        assert restored.auth.client_secret is not None
        assert restored.auth.client_secret.get_secret_value() == "plain-secret"
        assert restored.auth.refresh_token is not None
        assert restored.auth.refresh_token.get_secret_value() == "plain-rt"


def test_ui_secret_placeholder_never_echoes_secret_value() -> None:
    from jre_vidget.ui import _config_secret_placeholder

    assert _config_secret_placeholder(None) == "—"
    assert _config_secret_placeholder(SecretStr("super-secret-value")) == "(set)"
    assert "super-secret" not in _config_secret_placeholder(SecretStr("super-secret-value"))
