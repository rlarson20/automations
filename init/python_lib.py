#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "typer>=0.12",
#   "rich>=13.0",
#   "questionary>=2.0",
#   "tomli-w>=1.0",
#   "automations-parts",
# ]
#
# [tool.uv.sources]
# automations-parts = { path = "../parts" }
# ///
"""Scaffold a uv Python library with sane defaults.

Usage:
    uv run init/python_lib.py <name> [options]
"""

import subprocess
from pathlib import Path

import questionary
import typer
from rich.console import Console
from rich.panel import Panel

from automations_parts import git, github, precommit, toml_utils
from automations_parts.readme import ReadmeConfig, write_readme

app = typer.Typer(add_completion=False)
console = Console()


def die(msg: str) -> None:
    console.print(f"[bold red]error:[/] {msg}")
    raise SystemExit(1)


@app.command()
def main(
    name: str = typer.Argument(..., help="Project directory / package name"),
    private: bool = typer.Option(True, help="Create GitHub repo as private"),
    no_github: bool = typer.Option(
        False, "--no-github", help="Skip GitHub repo creation"
    ),
    description: str = typer.Option("", "--desc", help="Repo description"),
) -> None:
    root = Path(name)
    if root.exists():
        ok = questionary.confirm(
            f"'{root}' already exists. Continue?", default=False
        ).ask()
        if not ok:
            die("aborted")
    else:
        root.mkdir()

    console.print(f"\n[bold]scaffolding[/] [cyan]{name}[/]\n")

    # --- uv init --lib ---
    result = subprocess.run(
        ["uv", "init", "--lib", "--name", name.replace("-", "_"), "."],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        console.print(result.stderr)
        die("uv init failed")
    console.print("  [green]✓[/] uv init --lib")

    # --- dependency groups ---
    subprocess.run(
        ["uv", "add", "--group", "test", "pytest", "pytest-asyncio"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["uv", "add", "--group", "lint", "ruff", "mypy"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    toml_utils.set_dependency_groups(
        root / "pyproject.toml",
        {
            "dev": [
                {"include-group": "test"},
                {"include-group": "lint"},
            ]
        },
    )
    console.print("  [green]✓[/] dependency groups: test, lint, dev")

    # Patch pyproject metadata
    if description:
        toml_utils.patch(
            root / "pyproject.toml",
            **{"project": {"description": description}},
        )

    # --- tests/ stub ---
    tests = root / "tests"
    tests.mkdir(exist_ok=True)
    (tests / "__init__.py").touch()
    pkg = name.replace("-", "_")
    (tests / f"test_{pkg}.py").write_text(
        f'"""Tests for {pkg}."""\n\n\ndef test_placeholder() -> None:\n    assert True\n'
    )
    console.print("  [green]✓[/] tests/ stub")
    # README
    write_readme(
        root,
        ReadmeConfig(
            name=name,
            description=description or f"TODO: describe {name}.",
            install_commands=["uv sync --group dev"],
            usage_commands=["uv run pytest", "uv run ruff check ."],
        ),
    )
    console.print("  [green]✓[/] README.md")

    # --- pre-commit ---
    precommit.write_config(root, stacks=["python"])
    console.print("  [green]✓[/] .pre-commit-config.yaml")

    # --- git ---
    git.write_gitignore(root)
    git.git_init(root)
    console.print("  [green]✓[/] git init")

    precommit.install(root)
    console.print("  [green]✓[/] pre-commit install")

    git.initial_commit(root)
    console.print("  [green]✓[/] initial commit")

    # --- github ---
    if not no_github:
        github.create_repo(root, name=name, private=private, description=description)
        console.print("  [green]✓[/] github repo created and pushed")

    # --- done ---
    cmds = (
        f"  [dim]cd[/] {root}\n  [bold]uv run pytest[/]\n  [bold]uv run ruff check .[/]"
    )
    if not no_github:
        cmds += "\n  [bold]gh repo view --web[/]"
    console.print(
        Panel(f"[bold green]done.[/]\n\n{cmds}", title="next steps", expand=False)
    )


if __name__ == "__main__":
    app()
