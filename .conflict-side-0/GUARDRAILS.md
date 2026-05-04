# GUARDRAILS.md

Persistent safety constraints for jre-vidget. A living document — append Signs as failure
patterns are discovered.

```
Created: 2026-05-03
Last Updated: 2026-05-03
Total Signs: 7
```

---

## Privilege Boundaries

```
Allowed:
  Read:  src/, tests/, prompts/, docs/, .env.example, pyproject.toml
  Write: src/, tests/, docs/

Forbidden:
  - .env, .env.* (never read or write secrets)
  - ~/.vidget/config.json (user data — only touched at runtime, never in tests without tmp_path)
  - .git/**
  - .venv/**, site-packages/**
  - Any path outside this repository
```

---

## Rate Limits

| Limit | Threshold | Action |
|-------|-----------|--------|
| Tool calls per iteration | 10 | Force context rotation |
| Consecutive identical errors | 3 | Append Sign + stop |
| Context usage | 80% | Snapshot state + compact |

---

## SIGN #1: Engine ↔ UI Coupling

**Trigger:** About to import anything from `ui.py` inside `engine.py`

**Instruction:**
1. Stop immediately — do not add the import
2. Move the UI call to `cli.py` where it belongs
3. The engine returns data; the CLI layer renders it

**Reason:** `engine.py` must be importable and testable without Rich. Coupling breaks
unit tests and violates the single-responsibility principle.

**Provenance:** Manual — architecture constraint, phase-5 spec

---

## SIGN #2: Real Network in Tests

**Trigger:** About to write a test that calls `engine.fetch_info()` or `engine.download()`
without mocking `yt_dlp.YoutubeDL`

**Instruction:**
1. Stop — patch `yt_dlp.YoutubeDL` at the boundary
2. Use `unittest.mock.patch("jre_vidget.engine.yt_dlp.YoutubeDL")`
3. Tests must never hit the real network

**Reason:** Real network calls make tests slow, flaky, and dependent on external URLs.
Fox News / YouTube URLs change or geo-block.

**Provenance:** Manual — TESTING.md mocking strategy

---

## SIGN #3: Hardcoded Config Path

**Trigger:** Seeing a literal `~/.vidget/config.json` string anywhere in source code
(not in a comment or docstring)

**Instruction:**
1. Use `Path.home() / ".vidget" / "config.json"` — not a string literal
2. `CONFIG_PATH` constant lives in `models.py` and is imported everywhere else
3. Tests override `CONFIG_PATH` via `monkeypatch.setattr`

**Reason:** String literals for paths break cross-platform portability and cannot be
overridden in tests.

**Provenance:** Manual — phase-2 model spec

---

## SIGN #4: Bare print() in Production Modules

**Trigger:** Writing a `print(...)` call in `engine.py`, `models.py`, `config.py`,
or `checks.py`

**Instruction:**
1. Use `structlog.get_logger()` for informational/debug output in engine/config
2. Use `console.print(...)` (Rich) only in `ui.py` and `cli.py`
3. The no-print PostToolUse hook will warn on violations

**Reason:** `print()` bypasses logging infrastructure and cannot be suppressed
in library/programmatic use.

**Provenance:** Manual — AGENTS.md NEVER DO list; enforced by `.claude/hooks/no-print-check.sh`

---

## SIGN #5: Swallowed Download Exceptions

**Trigger:** Writing `except Exception: pass` or `except Exception: return None`
inside `engine.py`

**Instruction:**
1. Catch `yt_dlp.utils.DownloadError` specifically
2. On `DownloadError`: retry up to `config.retries` times, then return
   `DownloadResult(status=FAILED, error=str(e))`
3. Never swallow exceptions silently — always surface them in `DownloadResult.error`

**Reason:** Silent failures mean users see an empty output directory with no explanation.

**Provenance:** Manual — phase-6 retry spec

---

## Escalation Rules

Stop and ask a human immediately when:
- 3+ retries on the same coding problem with no progress
- Unsure which phase prompt to implement next
- A dependency needs to be added that isn't in the phase spec
- Any operation would touch files outside the declared Write scope

---

## SIGN #6: Rich Output Leaking to stdout When --json Active

**Trigger:** About to call `console.print(...)` or `ui.*()` on the normal `stdout` console
when the command was invoked with `--json`

**Instruction:**
1. Rich progress/spinner output must go to **stderr** — instantiate `Console(stderr=True)`
   for all non-data output in `ui.py`
2. When `--json` is active, `stdout` must contain **only** valid JSON — nothing else
3. Test: `vidget download URL --json | python3 -m json.tool` must succeed (no parse errors)

**Reason:** AI agents pipe `--json` output directly into parsers. Any stray Rich markup or
progress text on stdout causes `json.loads()` to throw, breaking the agent's workflow.

**Provenance:** CLI Best Practices for AI Agents (Notion) — Principle 1 (stdout/stderr split)

---

## SIGN #7: Non-Semantic or Missing Exit Code

**Trigger:** A command exits with `sys.exit(1)` or `raise typer.Exit(1)` for an error that
has a more specific code in the exit code table (codes 2–5, 130)

**Instruction:**
1. Check the exit code table in AGENTS.md → Agentic CLI Design Principles
2. Map the error to its specific code: auth=3, transient/retry=4, conflict=5, sigint=130
3. Never use exit code `1` when a more specific code applies
4. Ensure the structured JSON error on stdout includes a matching `"code"` field when `--json` is active

**Reason:** Agents use exit codes as their primary branching mechanism. A generic `1` on a
rate-limit error prevents the agent from applying correct retry logic.

**Provenance:** CLI Best Practices for AI Agents (Notion) — Principle 3 (semantic exit codes)

---

## Agent-Learned Signs

*No agent-learned signs yet. Append here as failure patterns are encountered.*
