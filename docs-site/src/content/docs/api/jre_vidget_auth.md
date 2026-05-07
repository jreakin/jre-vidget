---
title: jre_vidget.auth
description: "YouTube OAuth credential lifecycle for jre-vidget."
---


YouTube OAuth credential lifecycle for jre-vidget.

Handles browser-based OAuth login, token refresh, and logout.
No CLI, no Rich, no video logic.

Public API:
  login_browser(client_id, client_secret) -> AuthConfig
  get_credentials(auth) -> google.oauth2.credentials.Credentials
  publish_oauth_configured(auth) -> bool
  logout(cfg) -> AppConfig


## AuthError Objects

```python
class AuthError(Exception)
```

Raised when credentials are missing, invalid, or cannot be refreshed.


#### publish\_oauth\_configured

```python
def publish_oauth_configured(auth: AuthConfig) -> bool
```

True when OAuth client id, secret, and refresh token are all available (env or config).


#### read\_client\_id\_merged

```python
def read_client_id_merged(auth: AuthConfig) -> str | None
```

Resolved OAuth client id (env + ``auth``), same order as `get_credentials`.


#### read\_refresh\_token\_merged

```python
def read_refresh_token_merged(auth: AuthConfig) -> str | None
```

Resolved refresh token (env + ``auth``), same order as `get_credentials`.


#### login\_browser

```python
def login_browser(client_id: str, client_secret: str) -> AuthConfig
```

Run the browser-based OAuth2 flow on localhost (default port
`OAUTH_LOCAL_SERVER_PORT`, overridable via ``VIDGET_OAUTH_PORT``).

Opens the Google consent URL in the user's default browser, waits for the
redirect callback, and returns an AuthConfig with refresh_token populated.

The caller is responsible for persisting the result to AppConfig.


#### get\_credentials

```python
def get_credentials(auth: AuthConfig) -> Credentials
```

Return valid, refreshed Google credentials.

Reads client_id, client_secret, and refresh_token from auth, merged with
environment variables. **Client id** (first non-blank wins, in order):
``GCLOUD_CLIENT_ID``, ``GCLOUD_AUTH_CLIENT_ID``, ``VIDGET_CLIENT_ID``.
**Client secret:** ``GCLOUD_CLIENT_SECRET``, ``VIDGET_CLIENT_SECRET``.
**Refresh token:** ``GCLOUD_REFRESH_TOKEN``, ``VIDGET_REFRESH_TOKEN``.
Blank defined env values are skipped in favor of later keys or saved config.

Raises AuthError if credentials are missing or refresh fails.


#### logout

```python
def logout(cfg: AppConfig) -> AppConfig
```

Clear all YouTube credentials from cfg and persist to disk.

Returns the updated AppConfig.

