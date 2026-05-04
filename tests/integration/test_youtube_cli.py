"""Integration tests for YouTube CLI commands — mocked auth and publisher."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from google.auth.exceptions import GoogleAuthError
from pydantic import SecretStr
from typer.testing import CliRunner

from jre_vidget.cli import app
from jre_vidget.config import load_app_config, save_app_config
from jre_vidget.models import (
    AppConfig,
    AuthConfig,
    DownloadResult,
    DownloadStatus,
    PrivacyStatus,
    PublishResult,
    VideoInfo,
)

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolated_config_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use a per-test config file so CLI auth/publish tests never touch ~/.vidget."""
    import jre_vidget.config as vidget_cfg

    monkeypatch.setattr(vidget_cfg, "CONFIG_PATH", tmp_path / "config.json")


# ---------------------------------------------------------------------------
# auth login
# ---------------------------------------------------------------------------
class TestAuthLogin:
    def test_login_prompts_for_credentials(self, tmp_path: Path) -> None:
        mock_auth_config = AuthConfig(
            client_id="cid",
            client_secret=SecretStr("csecret"),
            refresh_token=SecretStr("rt"),
        )
        with patch("jre_vidget.cli_common.auth.login_browser", return_value=mock_auth_config):
            result = runner.invoke(
                app,
                ["auth", "login"],
                input="my-client-id\nmy-client-secret\n",
            )

        assert result.exit_code == 0
        assert "connected" in result.output.lower() or "success" in result.output.lower()

    def test_login_saves_credentials(self, tmp_path: Path) -> None:
        mock_auth_config = AuthConfig(
            client_id="cid",
            client_secret=SecretStr("csecret"),
            refresh_token=SecretStr("saved_token"),
        )
        with patch("jre_vidget.cli_common.auth.login_browser", return_value=mock_auth_config):
            runner.invoke(
                app,
                ["auth", "login"],
                input="cid\ncsecret\n",
            )

        cfg = load_app_config()
        assert cfg.auth.refresh_token is not None
        assert cfg.auth.refresh_token.get_secret_value() == "saved_token"

    def test_login_exits_1_on_google_auth_error(self) -> None:
        with patch(
            "jre_vidget.cli_common.auth.login_browser",
            side_effect=GoogleAuthError("access denied"),
        ):
            result = runner.invoke(
                app,
                ["auth", "login"],
                input="cid\ncsecret\n",
            )
        assert result.exit_code == 1
        combined = (result.stdout or "") + (result.stderr or "")
        assert "login failed" in combined.lower()
        assert "access denied" in combined.lower()

    def test_login_exits_1_on_unexpected_exception(self) -> None:
        with patch(
            "jre_vidget.cli_common.auth.login_browser",
            side_effect=RuntimeError("broken flow"),
        ):
            result = runner.invoke(
                app,
                ["auth", "login"],
                input="cid\ncsecret\n",
            )
        assert result.exit_code == 1
        combined = (result.stdout or "") + (result.stderr or "")
        assert "login failed" in combined.lower()
        assert "broken flow" in combined.lower()


# ---------------------------------------------------------------------------
# auth status
# ---------------------------------------------------------------------------
class TestAuthStatus:
    def test_shows_connected_when_token_present(self, tmp_path: Path) -> None:
        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token=SecretStr("rt"))
        save_app_config(cfg)

        result = runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        assert "connected" in result.output.lower()

    def test_shows_not_connected_when_no_token(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        assert "not connected" in result.output.lower() or "login" in result.output.lower()


# ---------------------------------------------------------------------------
# auth logout
# ---------------------------------------------------------------------------
class TestAuthLogout:
    def test_logout_clears_token(self, tmp_path: Path) -> None:
        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token=SecretStr("rt"))
        save_app_config(cfg)

        result = runner.invoke(app, ["auth", "logout"])
        assert result.exit_code == 0

        restored = load_app_config()
        assert restored.auth.refresh_token is None


# ---------------------------------------------------------------------------
# vidget publish
# ---------------------------------------------------------------------------
class TestPublishCommand:
    def test_publish_success(self, tmp_path: Path) -> None:
        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token=SecretStr("rt"))
        save_app_config(cfg)

        mock_result = PublishResult(
            video_id="abc123",
            url="https://youtube.com/watch?v=abc123",
            title="video",
            privacy=PrivacyStatus.PUBLIC,
        )
        with patch("jre_vidget.cli_common.publisher.upload", return_value=mock_result):
            result = runner.invoke(app, ["publish", str(video)])

        assert result.exit_code == 0
        assert "abc123" in result.output

    def test_publish_with_custom_title(self, tmp_path: Path) -> None:
        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token=SecretStr("rt"))
        save_app_config(cfg)

        with patch("jre_vidget.cli_common.publisher.upload") as mock_upload:
            mock_upload.return_value = PublishResult(
                video_id="x",
                url="https://youtube.com/watch?v=x",
                title="Custom",
                privacy=PrivacyStatus.PUBLIC,
            )
            runner.invoke(app, ["publish", str(video), "--title", "Custom Title"])

        publish_config = mock_upload.call_args[0][0]
        assert publish_config.title == "Custom Title"

    def test_publish_exits_3_when_not_authenticated(self, tmp_path: Path) -> None:
        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")

        from jre_vidget.auth import AuthError

        with patch("jre_vidget.cli_common.publisher.upload", side_effect=AuthError("not authed")):
            result = runner.invoke(app, ["publish", str(video)])

        assert result.exit_code == 3

    def test_publish_exits_1_on_publish_error(self, tmp_path: Path) -> None:
        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token=SecretStr("rt"))
        save_app_config(cfg)

        from jre_vidget.publisher import PublishError

        with patch("jre_vidget.cli_common.publisher.upload", side_effect=PublishError("bad")):
            result = runner.invoke(app, ["publish", str(video)])

        assert result.exit_code == 1

    def test_publish_privacy_flag(self, tmp_path: Path) -> None:
        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")

        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token=SecretStr("rt"))
        save_app_config(cfg)

        with patch("jre_vidget.cli_common.publisher.upload") as mock_upload:
            mock_upload.return_value = PublishResult(
                video_id="x",
                url="https://youtube.com/watch?v=x",
                title="t",
                privacy=PrivacyStatus.PRIVATE,
            )
            runner.invoke(app, ["publish", str(video), "--privacy", "private"])

        publish_config = mock_upload.call_args[0][0]
        assert publish_config.privacy == PrivacyStatus.PRIVATE


# ---------------------------------------------------------------------------
# download --publish flag
# ---------------------------------------------------------------------------
class TestDownloadWithPublish:
    def test_download_publish_calls_fetch_info_first(self, tmp_path: Path) -> None:
        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token=SecretStr("rt"))
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
            privacy=PrivacyStatus.PUBLIC,
        )

        with (
            patch("jre_vidget.cli_common.engine.fetch_info", return_value=mock_info) as mock_fi,
            patch("jre_vidget.cli_common.engine.download", return_value=mock_dl_result),
            patch("jre_vidget.cli_common.publisher.upload", return_value=mock_pub_result),
        ):
            result = runner.invoke(
                app,
                [
                    "download",
                    "https://example.com",
                    "--publish",
                    "--output",
                    str(tmp_path),
                ],
            )

        mock_fi.assert_called_once_with("https://example.com")
        assert result.exit_code == 0
        assert "xyz" in result.output

    def test_download_publish_uses_scraped_title(self, tmp_path: Path) -> None:
        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token=SecretStr("rt"))
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

        with (
            patch("jre_vidget.cli_common.engine.fetch_info", return_value=mock_info),
            patch("jre_vidget.cli_common.engine.download", return_value=mock_dl_result),
            patch("jre_vidget.cli_common.publisher.upload") as mock_pub,
        ):
            mock_pub.return_value = PublishResult(
                video_id="x",
                url="https://youtube.com/watch?v=x",
                title="Fox News Segment",
                privacy=PrivacyStatus.PUBLIC,
            )
            runner.invoke(
                app,
                [
                    "download",
                    "https://example.com",
                    "--publish",
                    "--output",
                    str(tmp_path),
                ],
            )

        publish_config = mock_pub.call_args[0][0]
        assert publish_config.title == "Fox News Segment"

    def test_download_publish_title_override(self, tmp_path: Path) -> None:
        cfg = AppConfig()
        cfg.auth = AuthConfig(refresh_token=SecretStr("rt"))
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

        with (
            patch("jre_vidget.cli_common.engine.fetch_info", return_value=mock_info),
            patch("jre_vidget.cli_common.engine.download", return_value=mock_dl_result),
            patch("jre_vidget.cli_common.publisher.upload") as mock_pub,
        ):
            mock_pub.return_value = PublishResult(
                video_id="x",
                url="https://youtube.com/watch?v=x",
                title="My Override",
                privacy=PrivacyStatus.PUBLIC,
            )
            runner.invoke(
                app,
                [
                    "download",
                    "https://example.com",
                    "--publish",
                    "--title",
                    "My Override",
                    "--output",
                    str(tmp_path),
                ],
            )

        publish_config = mock_pub.call_args[0][0]
        assert publish_config.title == "My Override"

    def test_download_without_publish_does_not_call_publisher(self, tmp_path: Path) -> None:
        fake_file = tmp_path / "video.mp4"
        fake_file.touch()

        mock_dl_result = DownloadResult(
            url="https://example.com",
            status=DownloadStatus.SUCCESS,
            filepath=fake_file,
            finished_at=datetime.now(),
        )

        with (
            patch("jre_vidget.cli_common.engine.download", return_value=mock_dl_result),
            patch("jre_vidget.cli_common.publisher.upload") as mock_pub,
        ):
            runner.invoke(
                app,
                ["download", "https://example.com", "--output", str(tmp_path)],
            )

        mock_pub.assert_not_called()
