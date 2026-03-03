"""pre-commit hook management."""

from pathlib import Path

from .run import run


# Always applied regardless of stack
GENERIC_HOOKS = """\
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
"""

PYTHON_HOOKS = """\
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
"""

RUST_HOOKS = """\
  - repo: local
    hooks:
      - id: cargo-fmt
        name: cargo fmt
        entry: cargo fmt --
        language: system
        types: [rust]
      - id: cargo-clippy
        name: cargo clippy
        entry: cargo clippy -- -D warnings
        language: system
        types: [rust]
        pass_filenames: false
"""

JS_HOOKS = """\
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.0.0
    hooks:
      - id: eslint
        additional_dependencies: ["eslint@9"]
"""

STACK_HOOKS: dict[str, str] = {
    "python": PYTHON_HOOKS,
    "rust": RUST_HOOKS,
    "js": JS_HOOKS,
}


def write_config(cwd: Path, stacks: list[str]) -> None:
    """Write .pre-commit-config.yaml combining generic + stack-specific hooks."""
    content = GENERIC_HOOKS
    for stack in stacks:
        if stack in STACK_HOOKS:
            content += STACK_HOOKS[stack]
    (cwd / ".pre-commit-config.yaml").write_text(content)


def install(cwd: Path) -> None:
    run(["uvx", "pre-commit", "install"], cwd=cwd)
