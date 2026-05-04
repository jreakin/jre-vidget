# GUARDRAILS.md

Persistent safety constraints for jre-vidget. A living document — append Signs as failure
patterns are discovered.

```
Created: 2026-05-03
Last Updated: 2026-05-03
Total Signs: 5
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

## Agent-Learned Signs

*No agent-learned signs yet. Append here as failure patterns are encountered.*
