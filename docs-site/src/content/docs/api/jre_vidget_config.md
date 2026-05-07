---
title: jre_vidget.config
description: "User config persistence for jre-vidget (Pydantic v2)."
---


User config persistence for jre-vidget (Pydantic v2).

``AppConfig`` is defined in ``jre_vidget.models``; this module reads and writes it
to ``CONFIG_PATH`` (``~/.vidget/config.json``). All persistence goes through
`load_app_config` and `save_app_config` (CLI commands, ``auth.logout``,
etc.). OAuth fields are written as plaintext on disk where set; on POSIX the
config directory uses mode ``0o700`` and the file ``0o600``.


#### load\_app\_config

```python
def load_app_config() -> AppConfig
```

Load user preferences from ``CONFIG_PATH``, or defaults if missing.


#### save\_app\_config

```python
def save_app_config(cfg: AppConfig) -> None
```

Write ``cfg`` to ``CONFIG_PATH`` with plaintext OAuth secrets where set.

