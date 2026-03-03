#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "typer>=0.12",
#   "rich>=13.0",
#   "questionary>=2.0",
#   "automations-parts",
# ]
#
# [tool.uv.sources]
# automations-parts = { path = "../parts" }
# ///
"""Scaffold a uv-managed notebook project with a project-scoped kernel.

Flavors:
  jupyter  uv init + ipykernel (venv-scoped) + notebooks/scratch.ipynb
  marimo   uv init + marimo + notebooks/scratch.py (reactive app)

Usage:
    uv run init/notebook.py <n> [--flavor jupyter|marimo] [options]
"""

import subprocess
from enum import StrEnum
from pathlib import Path

import questionary
import typer
from rich.console import Console
from rich.panel import Panel

from automations_parts import git, github, precommit, toml_utils
from automations_parts.readme import ReadmeConfig, write_readme

app = typer.Typer(add_completion=False)
console = Console()


class Flavor(StrEnum):
    jupyter = "jupyter"
    marimo = "marimo"


JUPYTER_STARTER = """\
{{
 "cells": [
  {{
   "cell_type": "code",
   "execution_count": null,
   "metadata": {{}},
   "outputs": [],
   "source": []
  }}
 ],
 "metadata": {{
  "kernelspec": {{
   "display_name": "{kernel_name}",
   "language": "python",
   "name": "{kernel_name}"
  }},
  "language_info": {{
   "name": "python"
  }}
 }},
 "nbformat": 4,
 "nbformat_minor": 5
}}
"""

MARIMO_STARTER = """\
import marimo

__generated_with = "0.10.0"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
"""


def die(msg: str) -> None:
    console.print(f"[bold red]error:[/] {msg}")
    raise SystemExit(1)


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode != 0:
        console.print(result.stderr)
        die(f"command failed: {' '.join(cmd)}")
    return result


def scaffold_jupyter(root: Path, kernel_name: str) -> None:
    run(["uv", "add", "--group", "notebook", "ipykernel"], cwd=root)
    toml_utils.set_dependency_groups(
        root / "pyproject.toml",
        {
            "notebook": ["ipykernel"],
            "dev": [{"include-group": "notebook"}],
        },
    )
    console.print("  [green]✓[/] ipykernel dependency group")

    run(
        [
            "uv",
            "run",
            "ipython",
            "kernel",
            "install",
            "--user",
            "--env",
            "VIRTUAL_ENV",
            str(root / ".venv"),
            f"--name={kernel_name}",
        ],
        cwd=root,
    )
    console.print(f"  [green]✓[/] kernel registered: {kernel_name}")

    notebooks = root / "notebooks"
    notebooks.mkdir()
    (notebooks / "scratch.ipynb").write_text(JUPYTER_STARTER.format(kernel_name=kernel_name))
    console.print("  [green]✓[/] notebooks/scratch.ipynb")


def scaffold_marimo(root: Path) -> None:
    run(["uv", "add", "--group", "notebook", "marimo"], cwd=root)
    toml_utils.set_dependency_groups(
        root / "pyproject.toml",
        {
            "notebook": ["marimo"],
            "dev": [{"include-group": "notebook"}],
        },
    )
    console.print("  [green]✓[/] marimo dependency group")

    notebooks = root / "notebooks"
    notebooks.mkdir()
    (notebooks / "scratch.py").write_text(MARIMO_STARTER)
    console.print("  [green]✓[/] notebooks/scratch.py")


def do_launch(root: Path, flavor: Flavor, notebook_file: Path) -> None:
    if flavor == Flavor.jupyter:
        console.print("\nlaunching jupyter lab…\n")
        subprocess.run(["uv", "run", "--with", "jupyter", "jupyter", "lab"], cwd=root)
    else:
        console.print(f"\nlaunching marimo edit {notebook_file.name}…\n")
        subprocess.run(["uv", "run", "marimo", "edit", str(notebook_file)], cwd=root)


@app.command()
def main(
    name: str = typer.Argument(..., help="Project directory name"),
    flavor: Flavor = typer.Option(Flavor.jupyter, "--flavor", help="jupyter or marimo"),
    description: str = typer.Option("", "--desc", help="Short project description"),
    private: bool = typer.Option(True, help="Create GitHub repo as private"),
    no_github: bool = typer.Option(False, "--no-github", help="Skip GitHub repo creation"),
    no_launch: bool = typer.Option(False, "--no-launch", help="Skip launching the notebook server"),
) -> None:
    root = Path(name).resolve()
    if root.exists():
        ok = questionary.confirm(f"'{name}' already exists. Continue?", default=False).ask()
        if not ok:
            die("aborted")
    else:
        root.mkdir()

    kernel_name = name.replace("-", "_")
    console.print(f"\n[bold]scaffolding[/] [cyan]{name}[/] ({flavor})\n")

    run(["uv", "init", "--name", kernel_name, "."], cwd=root)
    hello = root / "hello.py"
    if hello.exists():
        hello.unlink()
    console.print("  [green]✓[/] uv init")

    if flavor == Flavor.jupyter:
        scaffold_jupyter(root, kernel_name)
        gitignore_extra = ".ipynb_checkpoints/\n**/.ipynb_checkpoints/\n"
        notebook_file = root / "notebooks" / "scratch.ipynb"
        launch_hint = "uv run --with jupyter jupyter lab"
        kernel_line = f"\n  [dim]# kernel:[/] {kernel_name}  →  {root / '.venv'}"
    else:
        scaffold_marimo(root)
        gitignore_extra = "__pycache__/\n"
        notebook_file = root / "notebooks" / "scratch.py"
        launch_hint = "uv run marimo edit notebooks/scratch.py"
        kernel_line = ""

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

    git.write_gitignore(root, extra=gitignore_extra)
    precommit.write_config(root, stacks=["python"])
    git.git_init(root)
    precommit.install(root)
    console.print("  [green]✓[/] git init + pre-commit install")

    git.initial_commit(root)
    console.print("  [green]✓[/] initial commit")

    if not no_github:
        github.create_repo(root, name=name, private=private, description=description)
        console.print("  [green]✓[/] github repo created and pushed")

    console.print(
        Panel(
            f"[bold green]done.[/]\n\n  [dim]cd[/] {name}\n  [bold]{launch_hint}[/]{kernel_line}",
            title="next steps",
            expand=False,
        )
    )

    if not no_launch:
        do_launch(root, flavor, notebook_file)


if __name__ == "__main__":
    app()
