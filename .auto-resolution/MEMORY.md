# MEMORY.md
# Cap: 150 lines — clean after every 10 sessions
# Last Updated: 2026-05-03

## Current Task State

*No active task. Ready for phase implementation.*

---

## Completed Phases

*None yet — phases 1–6 prompts are written; implementation not started.*

---

## Key Decisions Made

- Project type: CLI worker (Typer + Rich + yt-dlp + ffmpeg)
- Package manager: uv
- Entry point: `vidget = "jre_vidget.cli:app"`
- Config path: `~/.vidget/config.json`
- No async — all engine operations are synchronous
- engine.py must never import ui.py (enforced by no-print hook)

---

## Known Failure Patterns

*None recorded yet. Append here as patterns are encountered.*

---

## Open Questions

*None.*

---

## Compaction Instructions

When context reaches 80% usage:
1. Record the current phase and last file touched above
2. Note any test failures or unresolved errors
3. Discard raw tool output — keep only conclusions
4. Preserve: current phase, open questions, failure patterns, key decisions
