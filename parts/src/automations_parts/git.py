"""Git operations."""

import subprocess
from pathlib import Path

from .run import run

DEFAULT_GITIGNORE = """\
# Python
__pycache__/
*.py[cod]
.venv/
dist/
*.egg-info/
.eggs/

# uv
uv.lock

# Editors
.idea/
.vscode/
*.swp
*.swo
.DS_Store

# Env
.env
.env.*
!.env.example
"""


def git_init(cwd: Path) -> None:
    run(["git", "init"], cwd=cwd)


def write_gitignore(cwd: Path, extra: str = "") -> None:
    content = DEFAULT_GITIGNORE
    if extra:
        content += "\n" + extra.strip() + "\n"
    (cwd / ".gitignore").write_text(content)


def initial_commit(cwd: Path, message: str = "chore: initial scaffold") -> None:
    run(["git", "add", "-A"], cwd=cwd)
    # pre-commit fixers (e.g. end-of-file-fixer on template SVGs) rewrite files and fail
    # the first attempt; stage their fixes and retry once. A second failure is real.
    first = subprocess.run(["git", "commit", "-m", message], cwd=cwd, capture_output=True)
    if first.returncode != 0:
        run(["git", "add", "-A"], cwd=cwd)
        run(["git", "commit", "-m", message], cwd=cwd)
