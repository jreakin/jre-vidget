---
name: Notion plan doc gaps
overview: "The Notion full-implementation plan is effectively complete in source, tests, and CI. Remaining work is small: align [ARCHITECTURE.md](ARCHITECTURE.md) with the post-split modules and fix stale guardrails that contradict [AGENTS.md](AGENTS.md). Optional follow-ups tighten `auth_cmd` exceptions and add a router-level web smoke test."
todos:
  - id: arch-module-map
    content: Update ARCHITECTURE.md overview + Module Responsibilities for github_workflow.py, publish_flow.py, youtube_urls.py
    status: completed
  - id: guardrails-sync
    content: "Fix GUARDRAILS.md SIGN #3 (CONFIG_PATH in config.py) and SIGN #4 (stdlib logging, not structlog)"
    status: completed
  - id: optional-auth-except
    content: (Optional) Narrow or document auth_cmd.py exceptions around login_browser
    status: completed
  - id: optional-web-router-smoke
    content: (Optional) Add one AppRouter / route smoke test if mocks stay lightweight
    status: completed
isProject: false
---

# Close remaining gaps from Notion reports plan

## What is already done (no action)

Cross-check against [.cursor/plans/notion_reports_full_implementation_b1f92034.plan.md](.cursor/plans/notion_reports_full_implementation_b1f92034.plan.md):

- **Refactor / CLI / engine:** `_BatchWorker`, coercion helpers, postprocessor hook + `_find_newest_output_file` ordering, [`src/jre_vidget/github_workflow.py`](src/jre_vidget/github_workflow.py), [`src/jre_vidget/publish_flow.py`](src/jre_vidget/publish_flow.py), `progress_hook_session` in [`src/jre_vidget/cli_common.py`](src/jre_vidget/cli_common.py), `Console(stderr=True)`, `youtube_upload_or_exit`, config I/O in [`src/jre_vidget/config.py`](src/jre_vidget/config.py) (not on `AppConfig` in models).
- **Security / ops:** `VIDGET_OAUTH_PORT` / `VIDGET_LOG_FORMAT` in auth, cli_common, [`.env.example`](.env.example), [docs/SETUP.md](docs/SETUP.md); [`.github/workflows/publish.yml`](.github/workflows/publish.yml) runs `uv run vidget auth status --strict`; [`.github/workflows/ci-tests.yml`](.github/workflows/ci-tests.yml) has yt-dlp import smoke; [RUNBOOK.md](RUNBOOK.md) documents YouTube API quota.
- **Docs deliverables:** Flat `--json` contract in [ARCHITECTURE.md](ARCHITECTURE.md); [MEMORY.md](MEMORY.md) refreshed; [docs/adr/](docs/adr/) has ADR-001–005 including yt-dlp / Typer / Pydantic / ffmpeg; PAT + `localStorage` risk in [docs/SETUP.md](docs/SETUP.md) and pointer in [README.md](README.md).
- **Tests:** [`tests/integration/test_youtube_cli.py`](tests/integration/test_youtube_cli.py) `TestDownloadPublishHistoryPipeline` covers mocked download + publish JSON shape + `history.append_upload_record`; [`web/src/test/smoke.test.tsx`](web/src/test/smoke.test.tsx) has Vitest + Testing Library smoke (2 cases).

**Minor plan-doc nit (ignore or fix in plan file only):** the scope table cites `history.build_youtube_watch_url`; the canonical helper is [`src/jre_vidget/youtube_urls.py`](src/jre_vidget/youtube_urls.py) `build_youtube_watch_url`, imported by history and publisher.

---

## Gap 1 — ARCHITECTURE module map (required)

[ARCHITECTURE.md](ARCHITECTURE.md) still describes orchestration only under `cli_common.py` and omits split modules the plan called out.

**Edits:**

- Extend the ASCII overview (lines ~9–23) with one branch each for `github_workflow.dispatch_publish_workflow`, `publish_flow` (title / `PublishConfig` assembly), and optionally `youtube_urls` (single source for watch URLs).
- Add rows to **Module Responsibilities** for:
  - `github_workflow.py` — `gh workflow run` for `publish.yml`
  - `publish_flow.py` — pure publish field resolution / `PublishConfig` build (no Typer/Rich)
  - `youtube_urls.py` — YouTube watch URL formatting (shared by publisher + history)

Keep the narrative that `cli_common.py` still wires Typer/Rich to engine/publisher; the new rows clarify **where** dispatch and publish assembly live after the split.

---

## Gap 2 — GUARDRAILS drift vs current repo rules (required)

[GUARDRAILS.md](GUARDRAILS.md) conflicts with implemented architecture and [AGENTS.md](AGENTS.md):

| Location | Stale text | Correct alignment |
|----------|------------|-------------------|
| SIGN #3 (~81–82) | `CONFIG_PATH` in `models.py` | `CONFIG_PATH` and persistence live in [`src/jre_vidget/config.py`](src/jre_vidget/config.py); tests patch `jre_vidget.config.CONFIG_PATH` (see [TESTING.md](TESTING.md) / integration tests). |
| SIGN #4 (~97) | `structlog.get_logger()` in engine/config | Project uses **stdlib `logging`** in non-CLI modules per AGENTS.md; instruct `logging.getLogger(__name__)` (and Rich only in `cli.py` / `ui.py`). |

Update **Reason** / **Provenance** lines only if needed so the guardrail still reads as intentional policy.

---

## Gap 3 — `auth_cmd` exception narrowing (optional)

[`src/jre_vidget/commands/auth_cmd.py`](src/jre_vidget/commands/auth_cmd.py) uses a broad `except Exception` around `login_browser` with an explicit noqa. The original plan asked to narrow this.

**If you want strict alignment:** identify the small set of exception types raised by `google_auth_oauthlib` / browser flow (e.g. `OSError`, `ValueError`, library-specific errors), catch those, and re-raise unexpected exceptions after logging—or document in-module why broad catch is required and drop this task.

**Risk:** missing a real-world failure mode and surfacing a raw traceback instead of the friendly message; treat as low priority unless you want belt-and-suspenders typing.

---

## Gap 4 — Web smoke “App shell” (optional)

Current smoke tests cover [`ErrorBoundary`](web/src/components/ErrorBoundary.tsx) and [`TopBar`](web/src/components/TopBar.tsx). The plan wording mentioned “critical routes or App shell.”

**Optional enhancement:** one test that mounts [`AppRouter`](web/src/router.tsx) (or the router tree) with TanStack Router’s test utilities / memory history so a default route renders without network—only if the router and providers are easy to stub (PAT/query). Skip if it requires heavy mocks; the plan’s “1–3 tests minimum” is already satisfied.

---

## Validation (after edits)

- Docs-only: skim links in ARCHITECTURE for broken paths.
- If Gap 3 or 4 implemented: `uv run pytest` and `npm test` in `web/` (or project-standard web test command).

No GitNexus impact analysis is required for markdown-only Gap 1–2; run it if you touch Python (Gap 3).
