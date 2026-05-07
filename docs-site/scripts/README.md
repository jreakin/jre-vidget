# Docs-site scripts

## `python-autodoc.json`

Configure [`build-python-docs.mjs`](./build-python-docs.mjs):

| Field | Meaning |
|-------|---------|
| `searchPath` | Directory added to Python import path — must contain the `jre_vidget` package (`../src` from `docs-site/`). |
| `modules` | Fully-qualified names to pass to pydoc-markdown (`jre_vidget.engine`, …). |
| `outputDir` | Generated Markdown under `docs-site/` (default `src/content/docs/api`). |

## Generate API Markdown

From repo root (recommended):

```bash
uv sync --extra dev
cd docs-site && bun run docs:python
```

Then `bun run dev` and open `/api/` locally (with dev base) or build with `ASTRO_BASE` set as in `docs-site/README.md`.

Add or remove `modules` entries when the public API surface changes.
