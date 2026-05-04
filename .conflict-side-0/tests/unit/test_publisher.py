"""Tests for publisher.py — mocked YouTube API, no real uploads."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jre_vidget.auth import AuthError
from jre_vidget.models import AuthConfig, PublishConfig, PublishResult
from jre_vidget.publisher import PublishError, upload


@pytest.fixture()
def video_file(tmp_path: Path) -> Path:
    f = tmp_path / "video.mp4"
    f.write_bytes(b"fake video content")
    return f


@pytest.fixture()
def auth_config() -> AuthConfig:
    return AuthConfig(
        client_id="cid",
        client_secret="csecret",
        refresh_token="rt",
    )


@pytest.fixture()
def publish_config(video_file: Path) -> PublishConfig:
    return PublishConfig(
        filepath=video_file,
        title="Test Video",
        description="A test description",
        privacy="public",
    )


class TestUploadSuccess:
    def test_returns_publish_result(
        self, publish_config: PublishConfig, auth_config: AuthConfig
    ) -> None:
        mock_creds = MagicMock()
        mock_youtube = MagicMock()
        mock_insert = MagicMock()
        mock_insert.next_chunk.side_effect = [(None, {"id": "abc123"})]
        mock_youtube.videos.return_value.insert.return_value = mock_insert

        with (
            patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds),
            patch("jre_vidget.publisher.build", return_value=mock_youtube),
            patch("jre_vidget.publisher.MediaFileUpload"),
        ):
            result = upload(publish_config, auth_config)

        assert isinstance(result, PublishResult)
        assert result.video_id == "abc123"
        assert result.url == "https://youtube.com/watch?v=abc123"
        assert result.title == "Test Video"
        assert result.privacy == "public"
        assert result.removed_local_file is False

    def test_insert_called_with_correct_metadata(
        self, publish_config: PublishConfig, auth_config: AuthConfig
    ) -> None:
        mock_creds = MagicMock()
        mock_youtube = MagicMock()
        mock_insert = MagicMock()
        mock_insert.next_chunk.side_effect = [(None, {"id": "vid1"})]
        mock_youtube.videos.return_value.insert.return_value = mock_insert

        with (
            patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds),
            patch("jre_vidget.publisher.build", return_value=mock_youtube),
            patch("jre_vidget.publisher.MediaFileUpload"),
        ):
            upload(publish_config, auth_config)

        insert_call = mock_youtube.videos.return_value.insert.call_args
        body = insert_call[1]["body"]
        assert body["snippet"]["title"] == "Test Video"
        assert body["snippet"]["description"] == "A test description"
        assert body["status"]["privacyStatus"] == "public"

    def test_media_file_upload_resumable(
        self, publish_config: PublishConfig, auth_config: AuthConfig, video_file: Path
    ) -> None:
        mock_creds = MagicMock()
        mock_youtube = MagicMock()
        mock_youtube.videos.return_value.insert.return_value.next_chunk.side_effect = [
            (None, {"id": "x"})
        ]

        with (
            patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds),
            patch("jre_vidget.publisher.build", return_value=mock_youtube),
            patch("jre_vidget.publisher.MediaFileUpload") as mock_media,
        ):
            upload(publish_config, auth_config)

        mock_media.assert_called_once_with(str(video_file), resumable=True)


class TestUploadWithProgressHook:
    def test_progress_hook_called(
        self, publish_config: PublishConfig, auth_config: AuthConfig
    ) -> None:
        mock_creds = MagicMock()
        mock_youtube = MagicMock()
        # Simulate two chunks then completion
        mock_request = MagicMock()
        mock_request.next_chunk.side_effect = [
            (MagicMock(total_size=100, resumable_progress=50), None),
            (None, {"id": "done123"}),
        ]
        mock_youtube.videos.return_value.insert.return_value = mock_request

        progress_calls: list[tuple[int, int]] = []

        def hook(uploaded: int, total: int) -> None:
            progress_calls.append((uploaded, total))

        with (
            patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds),
            patch("jre_vidget.publisher.build", return_value=mock_youtube),
            patch("jre_vidget.publisher.MediaFileUpload"),
        ):
            result = upload(publish_config, auth_config, progress_hook=hook)

        assert result.video_id == "done123"
        assert len(progress_calls) >= 1


class TestUploadRemoveAfterUpload:
    def test_removes_file_on_success(self, tmp_path: Path, auth_config: AuthConfig) -> None:
        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")
        config = PublishConfig(
            filepath=video,
            title="t",
            remove_after_upload=True,
        )

        mock_creds = MagicMock()
        mock_youtube = MagicMock()
        mock_youtube.videos.return_value.insert.return_value.next_chunk.side_effect = [
            (None, {"id": "r1"})
        ]

        with (
            patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds),
            patch("jre_vidget.publisher.build", return_value=mock_youtube),
            patch("jre_vidget.publisher.MediaFileUpload"),
        ):
            result = upload(config, auth_config)

        assert not video.exists()
        assert result.removed_local_file is True

    def test_does_not_remove_file_on_failure(self, tmp_path: Path, auth_config: AuthConfig) -> None:
        from googleapiclient.errors import HttpError

        video = tmp_path / "video.mp4"
        video.write_bytes(b"data")
        config = PublishConfig(
            filepath=video,
            title="t",
            remove_after_upload=True,
        )

        mock_http_error = HttpError(
            resp=MagicMock(status=403),
            content=b'{"error": {"message": "quota exceeded"}}',
        )
        mock_creds = MagicMock()
        mock_youtube = MagicMock()
        mock_youtube.videos.return_value.insert.return_value.next_chunk.side_effect = (
            mock_http_error
        )

        with (
            patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds),
            patch("jre_vidget.publisher.build", return_value=mock_youtube),
            patch("jre_vidget.publisher.MediaFileUpload"),
            pytest.raises(PublishError),
        ):
            upload(config, auth_config)

        assert video.exists()  # file NOT deleted on failure


class TestUploadErrors:
    def test_raises_auth_error_when_not_configured(self, publish_config: PublishConfig) -> None:
        auth = AuthConfig()  # no credentials

        with (
            patch(
                "jre_vidget.publisher.auth.get_credentials",
                side_effect=AuthError("Run 'vidget auth login'"),
            ),
            pytest.raises(AuthError),
        ):
            upload(publish_config, auth)

    def test_raises_publish_error_on_http_error(
        self, publish_config: PublishConfig, auth_config: AuthConfig
    ) -> None:
        from googleapiclient.errors import HttpError

        mock_creds = MagicMock()
        mock_http_error = HttpError(
            resp=MagicMock(status=400),
            content=b'{"error": {"message": "invalid title"}}',
        )
        mock_youtube = MagicMock()
        mock_youtube.videos.return_value.insert.return_value.next_chunk.side_effect = (
            mock_http_error
        )

        with (
            patch("jre_vidget.publisher.auth.get_credentials", return_value=mock_creds),
            patch("jre_vidget.publisher.build", return_value=mock_youtube),
            patch("jre_vidget.publisher.MediaFileUpload"),
            pytest.raises(PublishError),
        ):
            upload(publish_config, auth_config)

    def test_raises_publish_error_on_missing_file(
        self, auth_config: AuthConfig, tmp_path: Path
    ) -> None:
        config = PublishConfig(
            filepath=tmp_path / "nonexistent.mp4",
            title="t",
        )
        with pytest.raises(PublishError, match="File not found"):
            upload(config, auth_config)
