## Summary

<!-- One sentence: what does this PR do and why? -->

## Changes

<!-- List the files changed and what changed in each. -->

## Testing

<!-- How did you verify this works? What test cases cover it? -->

---

## Checklist

- [ ] `uv run ruff check src/ tests/` — no lint errors
- [ ] `uv run ruff format --check src/ tests/` — no format violations
- [ ] `uv run ty check src/ tests/` — no type errors
- [ ] `uv run pytest` — all tests pass
- [ ] `uv run pytest --cov=src --cov-report=term-missing` — coverage maintained or improved
- [ ] New behaviour covered by unit tests in `tests/unit/`
- [ ] No bare `print()` added to `engine.py`, `models.py`, `config.py`, or `checks.py`
- [ ] No new imports from `ui.py` inside `engine.py`
- [ ] Exit codes match the table in AGENTS.md (auth=3, transient=4, conflict=5)
- [ ] `AGENTS.md` Project Structure updated if new files were added
- [ ] Prompt updated in `prompts/phase-*/current.md` if phase spec changed
