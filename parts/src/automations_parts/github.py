"""GitHub operations via gh CLI."""

from pathlib import Path

from .run import run


def create_repo(
    cwd: Path,
    name: str,
    private: bool = True,
    description: str = "",
) -> None:
    """Create a GitHub repo and push. Assumes git is already initialized + committed."""
    cmd = [
        "gh",
        "repo",
        "create",
        name,
        "--private" if private else "--public",
        "--source",
        ".",
        "--remote",
        "origin",
        "--push",
    ]
    if description:
        cmd += ["--description", description]
    run(cmd, cwd=cwd)
