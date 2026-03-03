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
"""Language-agnostic project scaffolder: git + gh + pre-commit + README stub.

Intended as the base for exotic stacks (Julia, Haskell, Gleam, Lean, Erlang, etc.)
where the language toolchain does its own init — this script handles everything around it.

Usage:
    uv run init/generic.py <name> [options]

    # Typical exotic-stack flow:
    uv run init/generic.py my-gleam-project --lang gleam --no-commit
    cd my-gleam-project && gleam new .
    git add -A && git commit -m "chore: gleam new"
"""

from pathlib import Path

import questionary
import typer
from rich.console import Console
from rich.panel import Panel

from automations_parts import git, github, precommit
from automations_parts.readme import ReadmeConfig, write_readme

app = typer.Typer(add_completion=False)
console = Console()

KNOWN_LANGS = [
    "gleam",
    "erlang",
    "elixir",
    "haskell",
    "julia",
    "lean",
    "ocaml",
    "zig",
    "other",
]

LANG_GITIGNORE: dict[str, str] = {
    "gleam": "build/\n_build/\n",
    "erlang": "_build/\n*.beam\n*.ez\nrebar3.crashdump\n",
    "elixir": "_build/\ndeps/\n*.ez\n.elixir_ls/\n",
    "haskell": "dist-newstyle/\n.stack-work/\n*.hi\n*.o\n",
    "julia": "Manifest.toml\n*.jl.*.cov\n*.jl.cov\n*.jl.mem\n",
    "lean": ".lake/\n",
    "ocaml": "_build/\n*.install\n*.byte\n*.native\n",
    "zig": "zig-out/\nzig-cache/\n",
}

LANG_INIT_HINTS: dict[str, str] = {
    "gleam": "gleam new .",
    "erlang": "rebar3 new app .",
    "elixir": "mix new . --app <name>",
    "haskell": "cabal init  OR  stack new <name>",
    "julia": "julia -e 'using Pkg; Pkg.generate(\".\")'",
    "lean": "lake init <name>",
    "ocaml": "dune init project <name> .",
    "zig": "zig init",
}


def die(msg: str) -> None:
    console.print(f"[bold red]error:[/] {msg}")
    raise SystemExit(1)


@app.command()
def main(
    name: str = typer.Argument(..., help="Project directory name"),
    lang: str = typer.Option(
        "other", "--lang", help=f"Language hint ({', '.join(KNOWN_LANGS)})"
    ),
    description: str = typer.Option("", "--desc", help="Short project description"),
    private: bool = typer.Option(True, help="Create GitHub repo as private"),
    no_github: bool = typer.Option(
        False, "--no-github", help="Skip GitHub repo creation"
    ),
    no_commit: bool = typer.Option(
        False,
        "--no-commit",
        help="Skip initial commit (useful when lang toolchain needs to run first)",
    ),
) -> None:
    if lang not in KNOWN_LANGS:
        console.print(f"[yellow]warning:[/] unknown lang '{lang}', treating as 'other'")
        lang = "other"

    root = Path(name)
    if root.exists():
        ok = questionary.confirm(
            f"'{root}' already exists. Continue?", default=False
        ).ask()
        if not ok:
            die("aborted")
    else:
        root.mkdir()

    console.print(f"\n[bold]scaffolding[/] [cyan]{name}[/] ({lang})\n")

    # README
    hint = LANG_INIT_HINTS.get(lang, "")
    write_readme(
        root,
        ReadmeConfig(
            name=name,
            description=description or "TODO: describe this project.",
            sections=[("Setup", f"```\n{hint}\n```")] if hint else [],
        ),
    )

    # .gitignore: generic base + lang-specific extras
    git.write_gitignore(root, extra=LANG_GITIGNORE.get(lang, ""))
    console.print("  [green]✓[/] .gitignore")

    # pre-commit: generic only (no lang-specific hooks for exotic stacks)
    precommit.write_config(root, stacks=[])
    console.print("  [green]✓[/] .pre-commit-config.yaml")

    # git init
    git.git_init(root)
    precommit.install(root)
    console.print("  [green]✓[/] git init + pre-commit install")

    if not no_commit:
        git.initial_commit(root)
        console.print("  [green]✓[/] initial commit")
    else:
        console.print(
            "  [yellow]–[/] skipped initial commit (run your lang toolchain first)"
        )

    # GitHub
    if not no_github:
        github.create_repo(root, name=name, private=private, description=description)
        console.print("  [green]✓[/] github repo created and pushed")

    # Next steps
    hint = LANG_INIT_HINTS.get(lang)
    toolchain_line = (
        f"\n  [bold]{hint}[/]    [dim]# init language toolchain[/]" if hint else ""
    )
    commit_reminder = (
        "\n  [bold]git add -A && git commit -m 'chore: lang init'[/]"
        if no_commit
        else ""
    )

    console.print(
        Panel(
            f"[bold green]done.[/]\n\n"
            f"  [dim]cd[/] {root}"
            f"{toolchain_line}"
            f"{commit_reminder}",
            title="next steps",
            expand=False,
        )
    )


if __name__ == "__main__":
    app()
