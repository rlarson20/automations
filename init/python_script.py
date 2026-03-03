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
"""Scaffold a standalone PEP 723 Python script with git + gh + pre-commit.

Produces a single executable script with inline metadata, not a package.
For libraries/packages, use init/python_lib.py instead.

Usage:
    uv run init/python_script.py <name> [options]
"""

from pathlib import Path

import questionary
import typer
from automations_parts import git, github, precommit
from automations_parts.readme import ReadmeConfig, write_readme
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(add_completion=False)
console = Console()


def _check_not_in_uv_workspace() -> None:
    """Abort if cwd is inside a uv workspace — would pollute parent lock."""
    import tomllib
    from pathlib import Path

    for parent in Path.cwd().parents:
        p = parent / "pyproject.toml"
        if p.exists():
            try:
                data = tomllib.loads(p.read_text())
                if "workspace" in data.get("tool", {}).get("uv", {}):
                    console.print(
                        f"[bold red]error:[/] {parent} is a uv workspace root. "
                        "Run init scripts from outside it."
                    )
                    raise SystemExit(1)
            except tomllib.TOMLDecodeError:
                pass


SCRIPT_TEMPLATE = '''\
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "rich>=13.0",
# ]
# ///
"""{description}"""

from rich.console import Console

console = Console()


def main() -> None:
    console.print("hello from {name}")


if __name__ == "__main__":
    main()
'''


def die(msg: str) -> None:
    console.print(f"[bold red]error:[/] {msg}")
    raise SystemExit(1)


@app.command()
def main(
    name: str = typer.Argument(..., help="Script name (without .py)"),
    description: str = typer.Option("", "--desc", help="One-line script description"),
    private: bool = typer.Option(True, help="Create GitHub repo as private"),
    no_github: bool = typer.Option(False, "--no-github", help="Skip GitHub repo creation"),
) -> None:
    _check_not_in_uv_workspace()
    root = Path(name)
    if root.exists():
        ok = questionary.confirm(f"'{root}' already exists. Continue?", default=False).ask()
        if not ok:
            die("aborted")
    else:
        root.mkdir()

    script_file = name.replace("-", "_") + ".py"
    console.print(f"\n[bold]scaffolding[/] [cyan]{name}/{script_file}[/]\n")

    # Script
    (root / script_file).write_text(
        SCRIPT_TEMPLATE.format(
            name=name,
            description=description or f"TODO: describe {name}",
        )
    )
    (root / script_file).chmod(0o755)
    console.print(f"  [green]✓[/] {script_file}")

    # README
    write_readme(
        root,
        ReadmeConfig(
            name=name,
            description=description or f"TODO: describe {name}.",
            usage_commands=[f"uv run {script_file}"],
            sections=[("Add dependencies", f"`uv add --script {script_file} <pkg>`")],
        ),
    )
    console.print("  [green]✓[/] README.md")

    git.write_gitignore(root)
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
            f"[bold green]done.[/]\n\n"
            f"  [dim]cd[/] {root}\n"
            f"  [bold]uv run {script_file}[/]\n"
            f"  [dim]# add deps:[/] uv add --script {script_file} <pkg>",
            title="next steps",
            expand=False,
        )
    )


if __name__ == "__main__":
    app()
