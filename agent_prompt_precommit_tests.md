# Task: Add pre-commit + pytest to the `automations` repo itself

## Context

This is a personal project scaffolding repo. Structure:

```
automations/
  init/
    generic.py, hugo.py, js.py, notebook.py, python_lib.py, python_script.py, rust.py
  parts/
    src/automations_parts/
      git.py, github.py, precommit.py, readme.py, run.py, toml_utils.py
    pyproject.toml        # automations-parts package
    uv.lock
  cleanup/
    remove_kernel.py
  update.py
  README.md
```

Key facts:
- All `init/` scripts are standalone PEP 723 scripts (`uv run`-able), not importable modules
- `parts/` is a proper installable package (`automations-parts`) with src layout
- No top-level `pyproject.toml` or venv exists yet — you will create both
- Python 3.12+. Use `uv` for all package management. No `pip`.
- Linting: ruff + mypy. Testing: pytest.
- pre-commit runs via `uvx pre-commit` — do not `pip install pre-commit`

---

## Step 1: Top-level pyproject.toml

Create `automations/pyproject.toml`:

```toml
[project]
name = "automations"
version = "0.1.0"
description = "Personal project scaffolding scripts"
requires-python = ">=3.12"
dependencies = []

[tool.uv.sources]
automations-parts = { path = "parts" }

[dependency-groups]
lint = ["ruff>=0.8", "mypy>=1.13"]
test = ["pytest>=8.0", "pytest-mock>=3.14"]
dev = [
    { include-group = "lint" },
    { include-group = "test" },
]

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Then run:
```bash
uv sync --group dev
```

---

## Step 2: pre-commit config

Create `automations/.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: check-added-large-files
        args: ["--maxkb=500"]
      - id: check-case-conflict
      - id: mixed-line-ending

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: ["--fix"]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        files: ^parts/src/
        additional_dependencies: ["tomli-w>=1.0", "rich>=13.0"]
```

Note: mypy is scoped to `parts/src/` only. The `init/` scripts are PEP 723
standalone files — they import `automations-parts` as a path dep declared in
their inline metadata, which mypy cannot resolve without per-script venvs.
Linting `init/` with ruff is fine; type-checking is out of scope here.

Then run:
```bash
uvx pre-commit install
uvx pre-commit run --all-files  # fix any violations before writing tests
```

---

## Step 3: Tests

Create `automations/tests/` with the following files.

### `tests/__init__.py`
Empty.

### `tests/conftest.py`

```python
"""Shared fixtures for automations tests."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Return a temp directory suitable as a fake project root."""
    return tmp_path
```

### `tests/parts/test_toml_utils.py`

Test `automations_parts.toml_utils` — the only module with pure, side-effect-free
logic worth unit testing directly.

Cover:
- `read()` / `write()` round-trip: write a known dict, read it back, assert equal
- `patch()` shallow merge: existing key updated, unrelated keys preserved
- `patch()` deep merge: nested dict merged not replaced
- `set_dependency_groups()`: adds groups to a fresh pyproject, existing keys preserved

Use real temp files via `tmp_project` fixture. No mocks needed here.

### `tests/parts/test_readme.py`

Test `automations_parts.readme`.

Cover:
- `render()` with no optional fields: only title + license section present
- `render()` with description, install_commands, usage_commands: sections appear in
  correct order (title → description → install → usage → license)
- `render()` with extra `sections`: appear between usage and license
- `render()` license resolution priority:
  - explicit `cfg.license` wins over pyproject
  - pyproject PEP 639 string form (`license = "MIT"`) is read correctly
  - pyproject legacy dict form (`license = {text = "MIT License"}`) → "MIT"
  - fallback to "MIT" when neither is present
- `write_readme()`: file is actually written to disk with correct content

For license-from-pyproject tests, write a minimal `pyproject.toml` into
`tmp_project` and pass `root=tmp_project` to `render()`.

### `tests/parts/test_git.py`

Test `automations_parts.git` — specifically `write_gitignore()`.

Cover:
- Default content contains expected patterns (`__pycache__`, `.venv`, `.DS_Store`)
- `extra` kwarg is appended after the default block
- File is written to the correct path

Do NOT test `git_init` or `initial_commit` — these shell out to git and belong
in integration tests, not unit tests.

### `tests/parts/__init__.py`
Empty.

---

## Step 4: Verify

```bash
uv run pytest
uvx pre-commit run --all-files
```

All tests should pass. Fix any ruff/mypy violations surfaced by pre-commit before
committing. Do not suppress mypy errors with `# type: ignore` unless genuinely
necessary (e.g., a third-party stub gap) — fix them properly.

---

## Constraints

- No mocking of filesystem — use `tmp_path` / real files throughout
- No mocking of subprocess in unit tests — functions that shell out are not tested here
- Test file layout mirrors source layout: `tests/parts/` for `parts/src/automations_parts/`
- Keep tests minimal and fast — this is a scaffolding tool, not a web service
- All new Python files must pass `ruff` and `mypy --strict` (scoped as above)
