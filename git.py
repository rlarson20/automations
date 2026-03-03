"""Git operations."""

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
    run(["git", "commit", "-m", message], cwd=cwd)
