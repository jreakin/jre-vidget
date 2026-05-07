# DEPLOYMENTS.md
# jre-vidget — Deployment Reference

---

## Environments

| Environment | URL | Branch | Trigger |
|-------------|-----|--------|---------|
| **Web UI (GitHub Pages)** | `https://jreakin.github.io/jre-vidget/` | `gh-pages` | Push to `main` touching `web/**`, `docs-site/**`, or the deploy workflow |
| **Docs (Starlight, same Pages site)** | `https://jreakin.github.io/jre-vidget/docs/` | `gh-pages` | Same as web — merged into one `gh-pages` deploy |
| **Cloudflare Worker (OAuth proxy)** | `https://vidget-auth.*.workers.dev` | — | Push to `main` touching `worker/**` |
| **Python CLI** | PyPI (not published) / local install | `main` | Manual |

---

## Web UI — GitHub Pages

**Build → deploy pipeline:** `.github/workflows/deploy-web.yml`

```
Push to main (web/**, docs-site/**, src/jre_vidget/**, pyproject, uv.lock) → uv sync + docs:python → build web + Starlight → merge → gh-pages
```

- **Web** output: `web/dist/` (and the same files at the **root** of the `gh-pages` branch)
- **Docs** output: `docs-site/dist/` → copied to **`/docs/`** on Pages (e.g. `.../jre-vidget/docs/`)
- Single deploy avoids two workflows overwriting each other on `gh-pages`
- Env vars baked at build time: `VITE_APP_TITLE` from Actions **variables**; `VITE_GITHUB_REPO` from the variable if set, otherwise **`github.repository`** (forks need no extra variable).
- No server — fully static. GitHub Pages serves from the `gh-pages` branch root.

**First-time setup:**
1. Go to Settings → Pages → Source: Deploy from a branch → Branch: `gh-pages` / `/ (root)`
2. Run the bootstrap workflow to set `VITE_APP_TITLE` (and optionally `VITE_GITHUB_REPO` if you want an explicit override)
3. Trigger `deploy-web.yml` manually or push a change under `web/` or `docs-site/`

**Rollback:** Force-push a previous `gh-pages` commit, or re-run a previous `deploy-web.yml` run.

---

## Cloudflare Worker — OAuth Proxy

**Deploy pipeline:** `.github/workflows/deploy-worker.yml`

```
Push to main (worker/**) → npm ci → wrangler deploy
```

Requires GitHub Secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`

**Worker secrets** (set via `wrangler secret put` or Cloudflare dashboard):

| Secret | Value |
|--------|-------|
| `GITHUB_CLIENT_ID` | OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | OAuth App client secret |
| `ALLOWED_ORIGIN` | GitHub Pages URL (e.g. `https://jreakin.github.io/jre-vidget`) |

**Local deploy:**
```bash
cd worker
CLOUDFLARE_API_TOKEN=<token> npx wrangler deploy
npx wrangler secret put GITHUB_CLIENT_ID
```

**Rollback:** Deploy a previous version from the Cloudflare dashboard (Workers → Deployments).

---

## GitHub Actions — Publish Workflow

Not a deployment target per se, but the workflow that does the actual work:

```
workflow_dispatch (from web UI) → publish.yml
  → yt-dlp download on Actions runner
  → ffmpeg conversion
  → YouTube Data API v3 upload
  → append to uploads.json → push to main
```

Required secrets: Google OAuth client id (`GCLOUD_CLIENT_ID` and/or `GCLOUD_AUTH_CLIENT_ID`, or legacy `VIDGET_CLIENT_ID`), client secret (`GCLOUD_CLIENT_SECRET` or `VIDGET_CLIENT_SECRET`), refresh token (`GCLOUD_REFRESH_TOKEN` or `VIDGET_REFRESH_TOKEN`) — see `docs/SETUP.md`.
Optional: `VIDGET_REPORT_TOKEN` (auto-reports failures to upstream repo issues)

---

## Versioning

`release-please` manages the changelog and version bump PR automatically.
Versions follow semantic versioning driven by conventional commits on `main`.

- `feat:` → minor bump
- `fix:` / `perf:` → patch bump
- `feat!:` / `fix!:` → major bump

**Anchor tag** (required for release-please): `git tag v0.1.0 && git push origin v0.1.0`
