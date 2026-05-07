# jre-vidget docs site

[Astro Starlight](https://starlight.astro.build) documentation with the [@abstractdata/starlight-theme](https://www.npmjs.com/package/@abstractdata/starlight-theme) ([source](https://github.com/Abstract-Data/abstract-data-doc-theme)).

## Commands

```bash
cd docs-site
bun install
bun run dev
```

Regenerate **API Reference** pages from `src/jre_vidget` (requires repo-root `uv sync --extra dev`):

```bash
cd /path/to/jre-vidget
uv sync --extra dev
cd docs-site && bun run docs:python
```

Configuration: [`scripts/python-autodoc.json`](scripts/python-autodoc.json) and [`scripts/README.md`](scripts/README.md).

Build static output to `dist/`:

```bash
bun run build
bun run preview
```

## GitHub Pages base path

For a project site, the docs app must live under **`/<repo>/docs/`** on Pages. CI sets this automatically in [`.github/workflows/deploy-web.yml`](../.github/workflows/deploy-web.yml) via `ASTRO_BASE` and merges `web/dist` + `docs-site/dist` into a single `gh-pages` deploy.

Local production-style build (replace `jre-vidget` with your repo name if needed):

```bash
ASTRO_SITE=https://<user>.github.io ASTRO_BASE=/jre-vidget/docs/ bun run build
```

## Version chip

The Abstract Data theme shows `v0.1.5` in the header. Bump it in `astro.config.mjs` when you release a new **jre-vidget** version (keep in sync with `pyproject.toml`).
