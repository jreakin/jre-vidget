# Testing

Testing strategies, test categories, and CI integration for jre-vidget.

---

## Test Layout

```
tests/
├── unit/
│   ├── test_models.py            # Pydantic model validation, enums, computed fields
│   ├── test_properties_*.py      # Hypothesis property tests (pure models / build_ydl_opts)
│   ├── test_engine.py            # engine.py with mocked yt-dlp (no network)
│   └── test_config.py            # AppConfig load/save with tmp_path
└── integration/
    └── test_cli.py               # Full CLI via typer.testing.CliRunner (mocked engine)
```

---

## Running Tests

```bash
uv run pytest                               # All tests
uv run pytest tests/unit -x                # Unit tests, stop on first failure
uv run pytest tests/integration -v         # Integration tests, verbose
uv run pytest --cov=src --cov-report=term-missing  # With coverage
uv run pytest -k "test_download"           # Run matching tests only
uv run pytest tests/unit/test_properties_models.py tests/unit/test_properties_engine.py
```

---

## Property-based tests (Hypothesis)

Use **Hypothesis** for **pure, deterministic** invariants (formatting, enum maps, JSON round-trips, small finite grids). Prefer **example + mock** tests for CLI flows, `YoutubeDL` patching, and anything non-deterministic.

- Implementation: [`tests/unit/test_properties_models.py`](tests/unit/test_properties_models.py), [`tests/unit/test_properties_engine.py`](tests/unit/test_properties_engine.py)
- Dependency: `hypothesis` in the `dev` optional group ([`pyproject.toml`](pyproject.toml)); install with `uv sync --extra dev`
- Reference: [Hypothesis documentation](https://hypothesis.readthedocs.io/)

Property tests use explicit `@settings(max_examples=..., deadline=None)` to keep the unit suite within the performance targets below.

---

## Test Categories

### Unit Tests — `tests/unit/`

Test individual modules in isolation. **No real network, no real yt-dlp.**

```python
# ✅ GOOD — mock yt-dlp at the boundary
from unittest.mock import patch, MagicMock

def test_download_returns_success_result(tmp_path):
    fake_file = tmp_path / "video.mp4"
    fake_file.touch()

    with patch("jre_vidget.engine.yt_dlp.YoutubeDL") as MockYDL:
        mock_instance = MagicMock()
        MockYDL.return_value.__enter__.return_value = mock_instance
        result = engine.download(DownloadConfig(url="https://example.com",
                                                output_dir=tmp_path))

    assert result.status == DownloadStatus.SUCCESS
```

### Integration Tests — `tests/integration/`

Test full CLI command flow using Typer's `CliRunner`. Mock `engine` module, not yt-dlp.

```python
from typer.testing import CliRunner
from jre_vidget.cli import app

runner = CliRunner()

def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "vidget" in result.output

def test_keyboard_interrupt_handled(tmp_path):
    with patch("jre_vidget.cli.engine.download", side_effect=KeyboardInterrupt):
        result = runner.invoke(app, ["download", "https://x.com",
                                     "--output", str(tmp_path)])
    assert result.exit_code == 130
```

---

## Coverage Target

- Unit tests: **≥ 80%** on `models.py`, `engine.py`, `config.py`
- Integration tests: **≥ 70%** on `cli.py`
- Overall: **≥ 20 tests** across all files (phase-6 acceptance criterion)

---

## TDD Workflow for Each Phase

1. Write tests based on the phase prompt's acceptance criteria
2. Run — confirm they fail
3. Implement the module to pass the tests
4. Never modify test files during implementation

---

## Mocking Strategy

CLI command code imports services through ``jre_vidget.cli_common``. The thin ``jre_vidget.cli`` module **re-exports** ``auth``, ``checks``, ``engine``, ``publisher``, and ``ui`` as the same module objects, so either ``patch("jre_vidget.cli.engine.download", ...)`` or ``patch("jre_vidget.cli_common.engine.download", ...)`` works.

| What to mock | Where | How |
|-------------|-------|-----|
| `yt_dlp.YoutubeDL` | unit tests for engine | `unittest.mock.patch` |
| `engine.download` | CLI integration tests | `patch("jre_vidget.cli.engine.download")` or `patch("jre_vidget.cli_common.engine.download")` (same module object) |
| `engine.download_batch` | CLI batch tests | `patch("jre_vidget.cli.engine.download_batch")` or `patch("jre_vidget.cli_common.engine.download_batch")` |
| `load_app_config` | CLI tests with custom config | `monkeypatch` `CONFIG_PATH` |
| `CONFIG_PATH` | config tests | `monkeypatch.setattr` |

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Unit test suite | < 5s total |
| Integration test suite | < 10s total |
| Single model validation | < 1ms |
