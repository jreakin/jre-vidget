"""
User config persistence for jre-vidget (Pydantic v2).

``AppConfig`` is defined in ``jre_vidget.models``; this module reads and writes it
to ``CONFIG_PATH`` (``~/.vidget/config.json``). All persistence goes through
:func:`load_app_config` and :func:`save_app_config` (CLI commands, ``auth.logout``,
etc.). OAuth fields are written as plaintext on disk where set; on POSIX the
config directory uses mode ``0o700`` and the file ``0o600``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import SecretStr

from jre_vidget.models import AppConfig

CONFIG_PATH = Path.home() / ".vidget" / "config.json"


def _secret_plain(secret: SecretStr | None) -> str | None:
    return secret.get_secret_value() if secret is not None else None


def _app_config_to_disk_json(cfg: AppConfig) -> str:
    """JSON for disk with real OAuth secret strings (not ``model_dump_json`` masking)."""
    data: dict[str, Any] = {
        "output_dir": str(cfg.output_dir),
        "quality": cfg.quality.value,
        "format": cfg.format.value,
        "subtitles": cfg.subtitles,
        "max_concurrent": cfg.max_concurrent,
        "auth": {
            "client_id": cfg.auth.client_id,
            "client_secret": _secret_plain(cfg.auth.client_secret),
            "refresh_token": _secret_plain(cfg.auth.refresh_token),
        },
    }
    return json.dumps(data, indent=2)


def load_app_config() -> AppConfig:
    """Load user preferences from ``CONFIG_PATH``, or defaults if missing."""
    if CONFIG_PATH.exists():
        return AppConfig.model_validate_json(CONFIG_PATH.read_text(encoding="utf-8"))
    return AppConfig()


def save_app_config(cfg: AppConfig) -> None:
    """Write ``cfg`` to ``CONFIG_PATH`` with plaintext OAuth secrets where set."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        CONFIG_PATH.parent.chmod(0o700)
    CONFIG_PATH.write_text(_app_config_to_disk_json(cfg), encoding="utf-8")
    if os.name == "posix":
        CONFIG_PATH.chmod(0o600)
