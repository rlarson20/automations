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
"""Scaffold a Rust project with cargo + clippy/fmt pre-commit + gh.

Usage:
    uv run init/rust.py <name>
    uv run init/rust.py <name> --lib
    uv run init/rust.py <name> --no-github
"""

import shutil
import subprocess
from pathlib import Path

import questionary
import typer
from rich.console import Console
from rich.panel import Panel

from automations_parts import git, github, precommit
from automations_parts.readme import ReadmeConfig, write_readme

app = typer.Typer(add_completion=False)
console = Console()


def die(msg: str) -> None:
    console.print(f"[bold red]error:[/] {msg}")
    raise SystemExit(1)


def run(cmd: list[str], cwd: Path) -> None:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        console.print(result.stderr)
        die(f"command failed: {' '.join(cmd)}")


@app.command()
def main(
    name: str = typer.Argument(..., help="Project directory / crate name"),
    lib: bool = typer.Option(False, "--lib", help="Create a library crate (default: binary)"),
    private: bool = typer.Option(True, help="Create GitHub repo as private"),
    no_github: bool = typer.Option(False, "--no-github", help="Skip GitHub repo creation"),
    description: str = typer.Option("", "--desc", help="Short project description"),
) -> None:
    if not shutil.which("cargo"):
        die("cargo not found in PATH — install Rust from https://rustup.rs")

    root = Path(name)
    if root.exists():
        ok = questionary.confirm(f"'{root}' already exists. Continue?", default=False).ask()
        if not ok:
            die("aborted")
    else:
        root.mkdir()

    kind = "lib" if lib else "bin"
    console.print(f"\n[bold]scaffolding[/] [cyan]{name}[/] (cargo {kind})\n")

    # cargo init
    cargo_cmd = ["cargo", "init", "--name", name.replace("-", "_")]
    if lib:
        cargo_cmd.append("--lib")
    cargo_cmd.append(".")
    run(cargo_cmd, cwd=root)
    console.print(f"  [green]✓[/] cargo init --{kind}")

    # README
    run_cmd = "cargo test" if lib else "cargo run"
    write_readme(
        root,
        ReadmeConfig(
            name=name,
            description=description or f"TODO: describe {name}.",
            install_commands=["cargo build"],
            usage_commands=[run_cmd, "cargo test", "cargo clippy"],
        ),
    )
    console.print("  [green]✓[/] README.md")

    # gitignore — cargo init writes one, but we overwrite with our standard + /target
    git.write_gitignore(root, extra="target/\n")
    console.print("  [green]✓[/] .gitignore")

    # pre-commit
    precommit.write_config(root, stacks=["rust"])
    console.print("  [green]✓[/] .pre-commit-config.yaml")

    # git init — cargo init also inits git, so we reinit cleanly to get our hooks
    run(["git", "init"], cwd=root)
    precommit.install(root)
    console.print("  [green]✓[/] git init + pre-commit install")

    git.initial_commit(root)
    console.print("  [green]✓[/] initial commit")

    if not no_github:
        github.create_repo(root, name=name, private=private, description=description)
        console.print("  [green]✓[/] github repo created and pushed")

    cmds = f"  [dim]cd[/] {root}\n  [bold]{run_cmd}[/]\n  [bold]cargo clippy[/]"
    if not no_github:
        cmds += "\n  [bold]gh repo view --web[/]"
    console.print(Panel(f"[bold green]done.[/]\n\n{cmds}", title="next steps", expand=False))


if __name__ == "__main__":
    app()
