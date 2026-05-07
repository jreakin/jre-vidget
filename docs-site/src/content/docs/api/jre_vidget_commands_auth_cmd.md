---
title: jre_vidget.commands.auth_cmd
description: "vidget auth subcommands."
---


``vidget auth`` subcommands.


#### auth\_login

```python
def auth_login(
        show_refresh_token: bool = typer.
    Option(
        False,
        "--show-refresh-token",
        help=
        ("After success, print the refresh token for copying into GitHub Actions secrets "
         "(GCLOUD_REFRESH_TOKEN or VIDGET_REFRESH_TOKEN). Avoid shared or logged terminals."
         ),
    ),
        json_output: bool = typer.
    Option(
        False,
        "--json",
        help=
        "On success, print one JSON object to stdout with client_id and refresh_token only.",
    )) -> None
```

Connect your YouTube account via browser OAuth.


#### auth\_print\_token

```python
def auth_print_token(json_output: bool = typer.Option(
    False,
    "--json",
    help="Print only JSON (client_id + refresh_token) to stdout.",
)) -> None
```

Print the resolved refresh token (saved config or env) — no browser; for GitHub Actions setup.


#### auth\_status

```python
def auth_status(strict: bool = typer.Option(
    False,
    "--strict",
    help=
    ("Exit with code 3 if client id, secret, and refresh token are missing or blank "
     "(env + config). Does not contact Google; upload still validates the token."
     ),
)) -> None
```

Show YouTube connection status (env vars ``VIDGET_*`` count the same as saved config).


#### auth\_logout

```python
def auth_logout() -> None
```

Disconnect your YouTube account.

