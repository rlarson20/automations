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
"""Scaffold a JS/TS project with git + gh + pre-commit.

Flavors:
  vite        bun create vite (react-ts template)
  next        bun create next-app
  astro       bun create astro
  vanilla-ts  minimal hand-rolled TS setup, no framework

--serious layers on: ESLint + Prettier configs, stricter tsconfig.

Usage:
    uv run init/js.py <n> --flavor vite
    uv run init/js.py <n> --flavor next --serious --npm
"""

import json
import shutil
import subprocess
from enum import StrEnum
from pathlib import Path

import questionary
import typer
from automations_parts import git, github, precommit
from automations_parts.readme import ReadmeConfig, write_readme
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(add_completion=False)
console = Console()


class Flavor(StrEnum):
    vite = "vite"
    next = "next"
    astro = "astro"
    vanilla_ts = "vanilla-ts"


_DEFAULT_FLAVOR = typer.Option(Flavor.vite, "--flavor", help="vite | next | astro | vanilla-ts")

ESLINT_CONFIG = """\
import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    rules: {
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "warn",
    },
  },
);
"""

PRETTIER_CONFIG = """\
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
"""

# tsconfig additions for --serious
STRICT_TSCONFIG_ADDITIONS = {
    "strict": True,
    "noUncheckedIndexedAccess": True,
    "noImplicitReturns": True,
    "noFallthroughCasesInSwitch": True,
    "exactOptionalPropertyTypes": True,
}

VANILLA_TS_INDEX = """\
const main = (): void => {
  console.log("hello");
};

main();
"""

VANILLA_TS_CONFIG = """\
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
"""

VANILLA_PACKAGE_JSON = """\
{{
  "name": "{name}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "build": "tsc",
    "dev": "tsc --watch"
  }},
  "devDependencies": {{
    "typescript": "^5"
  }}
}}
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


def pkg(use_npm: bool) -> str:
    return "npm" if use_npm else "bun"


def scaffold_vite(root: Path, name: str, use_npm: bool) -> None:
    pm = pkg(use_npm)
    if pm == "bun":
        run(["bun", "create", "vite@latest", ".", "--template", "react-ts"], cwd=root)
        run(["bun", "install"], cwd=root)
    else:
        run(
            ["npm", "create", "vite@latest", ".", "--", "--template", "react-ts", "--yes"],
            cwd=root,
        )
        run(["npm", "install"], cwd=root)
    console.print("  [green]✓[/] vite (react-ts)")


def scaffold_next(root: Path, name: str, use_npm: bool, serious: bool) -> None:
    # next-app creates its own git repo; we'll reinit after
    base_cmd = [
        "bun" if not use_npm else "npx",
        "create-next-app@latest",
        ".",
        "--typescript",
        "--no-tailwind",
        "--no-src-dir",
        "--app",
        "--import-alias",
        "@/*",
        "--no-git",
    ]
    if serious:
        base_cmd.append("--eslint")
    else:
        base_cmd.append("--no-eslint")
    run(base_cmd, cwd=root)
    console.print("  [green]✓[/] next (app router, typescript)")


def scaffold_astro(root: Path, name: str, use_npm: bool) -> None:
    # pm = pkg(use_npm)
    run(
        [
            "bun" if not use_npm else "npx",
            "create-astro@latest",
            ".",
            "--template",
            "minimal",
            "--typescript",
            "strict",
            "--no-git",
            "--skip-houston",
            "--yes",
        ],
        cwd=root,
    )
    if use_npm:
        run(["npm", "install"], cwd=root)
    else:
        run(["bun", "install"], cwd=root)
    console.print("  [green]✓[/] astro (minimal, strict ts)")


def scaffold_vanilla_ts(root: Path, name: str, use_npm: bool) -> None:
    (root / "src").mkdir()
    (root / "src" / "index.ts").write_text(VANILLA_TS_INDEX)
    (root / "tsconfig.json").write_text(VANILLA_TS_CONFIG)
    (root / "package.json").write_text(VANILLA_PACKAGE_JSON.format(name=name))
    pm = pkg(use_npm)
    run([pm, "install"], cwd=root)
    console.print("  [green]✓[/] vanilla-ts (src/index.ts, tsconfig.json)")


def apply_serious(root: Path, flavor: Flavor, use_npm: bool) -> None:
    """Layer on ESLint + Prettier configs and tighten tsconfig."""
    pm = pkg(use_npm)

    # ESLint + Prettier deps (skip for next --serious, already included via create-next-app)
    if flavor != Flavor.next:
        run(
            [
                pm,
                "add",
                "-D",
                "eslint",
                "@eslint/js",
                "typescript-eslint",
                "prettier",
                "eslint-config-prettier",
            ],
            cwd=root,
        )

    (root / "eslint.config.mjs").write_text(ESLINT_CONFIG)
    (root / ".prettierrc").write_text(PRETTIER_CONFIG)
    (root / ".prettierignore").write_text("dist/\n.next/\n.astro/\nnode_modules/\n")
    console.print("  [green]✓[/] eslint.config.mjs + .prettierrc")

    # Patch tsconfig — vanilla-ts already has these; patch others
    if flavor != Flavor.vanilla_ts:
        tsconfig_path = root / "tsconfig.json"
        if tsconfig_path.exists():
            tsconfig = json.loads(tsconfig_path.read_text())
            tsconfig.setdefault("compilerOptions", {}).update(STRICT_TSCONFIG_ADDITIONS)
            tsconfig_path.write_text(json.dumps(tsconfig, indent=2) + "\n")
            console.print("  [green]✓[/] tsconfig.json (strict mode)")


@app.command()
def main(
    name: str = typer.Argument(..., help="Project directory name"),
    flavor: Flavor = _DEFAULT_FLAVOR,
    serious: bool = typer.Option(False, "--serious", help="Add ESLint, Prettier, strict tsconfig"),
    npm: bool = typer.Option(False, "--npm", help="Use npm instead of bun"),
    private: bool = typer.Option(True, help="Create GitHub repo as private"),
    no_github: bool = typer.Option(False, "--no-github", help="Skip GitHub repo creation"),
    description: str = typer.Option("", "--desc", help="Short project description"),
) -> None:
    if not npm and not shutil.which("bun"):
        console.print("[yellow]warning:[/] bun not found, falling back to npm")
        npm = True

    root = Path(name).resolve()
    if root.exists():
        ok = questionary.confirm(f"'{root}' already exists. Continue?", default=False).ask()
        if not ok:
            die("aborted")
    else:
        root.mkdir()

    mode = "serious" if serious else "throwaway"
    console.print(f"\n[bold]scaffolding[/] [cyan]{name}[/] ({flavor}, {pkg(npm)}, {mode})\n")

    match flavor:
        case Flavor.vite:
            scaffold_vite(root, name, npm)
        case Flavor.next:
            scaffold_next(root, name, npm, serious)
        case Flavor.astro:
            scaffold_astro(root, name, npm)
        case Flavor.vanilla_ts:
            scaffold_vanilla_ts(root, name, npm)

    if serious:
        apply_serious(root, flavor, npm)

    # pre-commit: js hooks only for --serious (requires eslint/prettier installed)
    precommit.write_config(root, stacks=["js"] if serious else [])
    git.write_gitignore(root, extra="node_modules/\ndist/\n.next/\n.astro/\n.vercel/\n")
    git.git_init(root)
    precommit.install(root)
    console.print("  [green]✓[/] git init + pre-commit install")

    git.initial_commit(root)
    console.print("  [green]✓[/] initial commit")

    if not no_github:
        github.create_repo(root, name=name, private=private, description=description)
        console.print("  [green]✓[/] github repo created and pushed")

    pm = pkg(npm)
    dev_cmd = {
        "vite": f"{pm} run dev",
        "next": f"{pm} run dev",
        "astro": f"{pm} run dev",
        "vanilla-ts": f"{pm} run dev",
    }

    write_readme(
        root,
        ReadmeConfig(
            name=name,
            description=description or f"TODO: describe {name}.",
            usage_commands=[dev_cmd[flavor]],
        ),
    )
    console.print(
        Panel(
            f"[bold green]done.[/]\n\n  [dim]cd[/] {name}\n  [bold]{dev_cmd[flavor]}[/]",
            title="next steps",
            expand=False,
        )
    )


if __name__ == "__main__":
    app()
