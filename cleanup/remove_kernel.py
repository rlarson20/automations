#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "questionary>=2.0",
#   "rich>=13.0",
#   "typer>=0.12",
# ]
# ///
"""Interactively remove Jupyter kernels from user kernel directories.

Shows all installed kernels as a checklist — pick what to delete.
Checks both macOS and Linux standard user kernel paths.

Usage:
    uv run cleanup/remove_kernel.py
    uv run cleanup/remove_kernel.py --dry-run
"""

import json
import shutil
from pathlib import Path

import questionary
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(add_completion=False)
console = Console()

# Standard user-writable kernel locations (system-wide paths are intentionally excluded)
KERNEL_DIRS = [
    Path.home() / ".local" / "share" / "jupyter" / "kernels",  # Linux + macOS (pip)
    Path.home() / "Library" / "Jupyter" / "kernels",  # macOS (some installers)
]


def find_kernels() -> list[dict]:
    """Return list of {name, display_name, path, venv, missing_venv} for all user kernels."""
    kernels = []
    seen = set()

    for kernel_dir in KERNEL_DIRS:
        if not kernel_dir.is_dir():
            continue
        for entry in sorted(kernel_dir.iterdir()):
            if not entry.is_dir() or entry.name in seen:
                continue
            seen.add(entry.name)

            kernel_json = entry / "kernel.json"
            if not kernel_json.exists():
                continue

            try:
                data = json.loads(kernel_json.read_text())
            except Exception:
                data = {}

            display_name = data.get("display_name", entry.name)

            # Detect venv path from env vars written by ipykernel install --env VIRTUAL_ENV
            venv_path: str | None = data.get("env", {}).get("VIRTUAL_ENV")
            missing_venv = bool(venv_path and not Path(venv_path).exists())

            kernels.append(
                {
                    "name": entry.name,
                    "display_name": display_name,
                    "path": entry,
                    "venv": venv_path,
                    "missing_venv": missing_venv,
                }
            )

    return kernels


def print_summary(kernels: list[dict]) -> None:
    table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    table.add_column("kernel name", style="cyan")
    table.add_column("display name")
    table.add_column("venv")

    for k in kernels:
        venv_cell = (
            f"[red]MISSING[/] {k['venv']}" if k["missing_venv"] else (k["venv"] or "[dim]—[/]")
        )
        table.add_row(k["name"], k["display_name"], venv_cell)

    console.print(table)
    console.print()


def die(msg: str) -> None:
    console.print(f"[bold red]error:[/] {msg}")
    raise SystemExit(1)


@app.command()
def main(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview removals without deleting"),
) -> None:
    kernels = find_kernels()

    if not kernels:
        console.print("[yellow]no user kernels found.[/]")
        raise SystemExit(0)

    console.print(f"\n[bold]found {len(kernels)} kernel(s):[/]\n")
    print_summary(kernels)

    # Build choices — pre-tick kernels with missing venvs as a hint, not a mandate
    choices = [
        questionary.Choice(
            title=(f"{k['name']}  [stale — venv missing]" if k["missing_venv"] else k["name"]),
            value=k["name"],
            checked=k["missing_venv"],
        )
        for k in kernels
    ]

    selected = questionary.checkbox(
        "Select kernels to remove (space to toggle, enter to confirm):",
        choices=choices,
    ).ask()

    if selected is None:
        die("aborted")

    if not selected:
        console.print("[dim]nothing selected, exiting.[/]")
        raise SystemExit(0)

    to_remove = [k for k in kernels if k["name"] in selected]

    console.print()
    for k in to_remove:
        tag = "[dim](dry run)[/] " if dry_run else ""
        console.print(f"  {tag}[red]removing[/] {k['name']}  →  {k['path']}")
        if not dry_run:
            shutil.rmtree(k["path"])

    noun = "kernel" if len(to_remove) == 1 else "kernels"
    suffix = " (dry run — nothing deleted)" if dry_run else ""
    console.print(f"\n[bold green]done.[/] removed {len(to_remove)} {noun}{suffix}")


if __name__ == "__main__":
    app()
