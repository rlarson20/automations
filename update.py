#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "typer>=0.12",
#   "rich>=13.0",
#   "questionary>=2.0",
# ]
# ///

"""Bump pre-commit hook revs across projects under a root directory.

Usage:
    uv run update.py                    # walk cwd
    uv run update.py --root ~/projects  # walk a specific root
    uv run update.py --root ~/projects --yes  # skip confirmation
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import questionary
import typer
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()


def die(msg: str) -> None:
    console.print(f"[bold red]error:[/] {msg}")
    raise SystemExit(1)


def find_configs(root: Path) -> list[Path]:
    return sorted(root.rglob(".pre-commit-config.yaml"))


def run_autoupdate(config: Path) -> tuple[bool, str]:
    """Run uvx pre-commit autoupdate in config's directory. Returns (ok, output)."""
    result = subprocess.run(
        ["uvx", "pre-commit", "autoupdate"],
        cwd=config.parent,
        text=True,
        capture_output=True,
    )
    output = result.stdout + result.stderr
    return result.returncode == 0, output


@app.command()
def main(
    root: Path = typer.Option(Path("."), "--root", help="Directory to search for configs"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip per-project confirmation"),
) -> None:
    root = root.expanduser().resolve()
    if not root.is_dir():
        die(f"not a directory: {root}")

    configs = find_configs(root)
    if not configs:
        console.print(f"[yellow]no .pre-commit-config.yaml files found under {root}[/]")
        raise SystemExit(0)
    console.print(f"\n[bold]found {len(configs)} config(s)[/]\n")

    # Checklist of which projects to update
    choices = [
        questionary.Choice(
            title=str(c.parent.relative_to(root))
            if str(c.parent.relative_to(root)) != "."
            else "(root)",
            value=c,
        )
        for c in configs
    ]

    if yes:
        selected = configs
    else:
        selected = questionary.checkbox(
            "Select projects to autoupdate (enter to confirm all / deselect to skip):",
            choices=[
                questionary.Choice(title=ch.title, value=ch.value, checked=True) for ch in choices
            ],
        ).ask()

    if selected is None:
        die("aborted")
    if not selected:
        console.print("[dim]nothing selected, exiting.[/]")
        raise SystemExit(0)

    console.print()
    ok_count = 0
    for config in selected:
        rel = str(config.parent.relative_to(root))
        label = rel if rel != "." else "(root)"
        console.print(f"  [bold]updating[/] {label} … ", end="")
        ok, output = run_autoupdate(config)
        if ok:
            # pre-commit autoupdate prints lines like "Updating X from Y to Z"
            updates = [l.strip() for l in output.splitlines() if l.strip().startswith("Updating")]
            if updates:
                console.print(f"[green]✓[/] {len(updates)} update(s)")
                for u in updates:
                    console.print(f"    [dim]{u}[/]")
            else:
                console.print("[dim]already up to date[/]")
            ok_count += 1
        else:
            console.print("[red]failed[/]")
            console.print(output)

    console.print(f"\n[bold green]done.[/] updated {ok_count}/{len(selected)} project(s)")


if __name__ == "__main__":
    app()
