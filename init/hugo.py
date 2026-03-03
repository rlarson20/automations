#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "questionary>=2.0",
#   "rich>=13.0",
#   "scripts-parts",
# ]
#
# [tool.uv.sources]
# automations-parts = { path = "../parts" }
# ///
"""Interactive scaffolder for a minimal Hugo site (based on simonwillison.net/til/hugo/basic)."""

import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from automations_parts import git, github, precommit
from automations_parts.readme import ReadmeConfig, write_readme

console = Console()


def die(msg: str) -> None:
    console.print(f"[bold red]error:[/] {msg}")
    sys.exit(1)


def write(path: Path, content: str, tree: Tree | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    if tree is not None:
        tree.add(f"[green]{path}[/]")


def scaffold(root: Path, site_title: str, base_url: str, author: str, tree: Tree) -> None:
    write(
        root / "layouts/_default/baseof.html",
        f"""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ .Title }}}} — {site_title}</title>
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/about">About</a>
    </nav>
    <main>
        {{{{ block "main" . }}}}{{{{ end }}}}
    </main>
    <footer>
        <p>&copy; {author}</p>
    </footer>
</body>
</html>
""",
        tree,
    )

    write(
        root / "layouts/_default/single.html",
        '{{ define "main" }}\n    {{ .Content }}\n{{ end }}\n',
        tree,
    )

    write(
        root / "layouts/index.html",
        '{{ define "main" }}\n    {{ .Content }}\n{{ end }}\n',
        tree,
    )

    write(
        root / "content/_index.md",
        f"""\
---
title: Welcome
---
# Welcome to {site_title}

This is the homepage. Edit `content/_index.md` to change this content.
""",
        tree,
    )

    write(
        root / "content/about.md",
        f"""\
---
title: About
---
# About

This is the about page for {site_title}.
""",
        tree,
    )


def init_hugo(root: Path, site_title: str, base_url: str) -> None:
    if not shutil.which("hugo"):
        console.print(
            "\n[yellow]hint:[/] hugo not found in PATH — skipping [italic]hugo new site[/]."
        )
        console.print("      install hugo, then run: [bold]hugo new site . --force[/]")
        return

    console.print("\nrunning [bold]hugo new site . --force[/]")
    result = subprocess.run(
        ["hugo", "new", "site", ".", "--force"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        console.print(result.stderr)
        die("hugo new site failed")

    toml_path = root / "hugo.toml"
    if toml_path.exists():
        toml_path.write_text(
            f"""\
baseURL = '{base_url}'
languageCode = 'en-us'
title = '{site_title}'
disableKinds = ['taxonomy', 'term']
"""
        )
        console.print(f"  [green]patched[/] {toml_path}")


def validate_url(val: str) -> bool | str:
    parsed = urlparse(val)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return True
    return "must be a full URL (e.g. https://example.com/)"


def validate_nonempty(val: str) -> bool | str:
    return True if val.strip() else "cannot be empty"


def main() -> None:
    console.print(Panel("[bold]Hugo site scaffolder[/]", expand=False))

    site_name = questionary.text(
        "Site directory name:", default="hugo-site", validate=validate_nonempty
    ).ask()
    if site_name is None:
        die("aborted")

    site_title = questionary.text(
        "Site title:", default="My Hugo Site", validate=validate_nonempty
    ).ask()
    if site_title is None:
        die("aborted")

    base_url = questionary.text(
        "Base URL:", default="https://example.com/", validate=validate_url
    ).ask()
    if base_url is None:
        die("aborted")

    author = questionary.text(
        "Author / footer text:", default="Me", validate=validate_nonempty
    ).ask()
    if author is None:
        die("aborted")

    create_gh = questionary.confirm("Create GitHub repo?", default=True).ask()
    private = False
    if create_gh:
        private = questionary.confirm("Private repo?", default=True).ask()

    root = Path(site_name)
    if root.exists():
        ok = questionary.confirm(f"'{root}' already exists. Continue anyway?", default=False).ask()
        if not ok:
            die("aborted")
    else:
        root.mkdir()

    tree = Tree(f"[bold]{root}/[/]")
    console.print()
    scaffold(root, site_title, base_url, author, tree)
    console.print(tree)

    init_hugo(root, site_title, base_url)
    write_readme(
        root,
        ReadmeConfig(
            name=site_name,
            description="",
            usage_commands=["hugo server", "hugo build"],
            sections=[
                (
                    "Deploy",
                    "Output in `./public/` — deploy anywhere that serves static files.",
                )
            ],
        ),
    )

    # git + pre-commit + github
    git.write_gitignore(root, extra="public/\nresources/_gen/\n.hugo_build.lock\n")
    precommit.write_config(root, stacks=[])  # generic only for Hugo
    git.git_init(root)
    precommit.install(root)
    git.initial_commit(root)
    console.print("  [green]✓[/] git init + pre-commit + initial commit")

    if create_gh:
        github.create_repo(root, name=site_name, private=private)
        console.print("  [green]✓[/] github repo created and pushed")

    console.print(
        Panel(
            f"[bold green]done.[/]\n\n"
            f"  [dim]cd[/] {root}\n"
            f"  [bold]hugo server[/]    [dim]# http://localhost:1313[/]\n"
            f"  [bold]hugo build[/]     [dim]# output → ./public/[/]",
            title="next steps",
            expand=False,
        )
    )


if __name__ == "__main__":
    main()
