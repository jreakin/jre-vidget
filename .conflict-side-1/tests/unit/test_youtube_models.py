"""Tests for YouTube publish models."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from jre_vidget.models import AppConfig, AuthConfig, PublishConfig, PublishResult


class TestAuthConfig:
    def test_defaults(self) -> None:
        cfg = AuthConfig()
        assert cfg.client_id is None
        assert cfg.client_secret is None
        assert cfg.refresh_token is None

    def test_round_trips_json(self) -> None:
        cfg = AuthConfig(
            client_id="cid",
            client_secret="csecret",
            refresh_token="rtoken",
        )
        restored = AuthConfig.model_validate_json(cfg.model_dump_json())
        assert restored.client_id == "cid"
        assert restored.refresh_token == "rtoken"

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
        for privacy in ("public", "unlisted", "private"):
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
            privacy="public",
        )
        assert "abc123" in result.url
        assert result.removed_local_file is False

    def test_removed_local_file_flag(self) -> None:
        result = PublishResult(
            video_id="x",
            url="https://youtube.com/watch?v=x",
            title="t",
            privacy="public",
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
        import jre_vidget.models as m

        monkeypatch.setattr(m, "CONFIG_PATH", tmp_path / "config.json")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token="mytoken")
        cfg.save()

        restored = AppConfig.load()
        assert restored.auth.refresh_token == "mytoken"
