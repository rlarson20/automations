"""Shared README renderer.

Provides a ReadmeConfig dataclass and render/write helpers used by all init/
scripts to produce consistent, non-drifting README.md files.

Stack-specific sections are deferred — use the `sections` escape hatch for now.

Usage:
    from automations_parts.readme import ReadmeConfig, write_readme

    write_readme(
        root,
        ReadmeConfig(
            name="my-project",
            description="Does the thing.",
            install_commands=["uv sync"],
            usage_commands=["uv run my_project/main.py"],
        ),
    )
"""

from __future__ import annotations

from typing import Any

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ReadmeConfig:
    name: str
    description: str = ""

    # Commands rendered verbatim inside a fenced code block.
    install_commands: list[str] = field(default_factory=list)
    usage_commands: list[str] = field(default_factory=list)

    # Arbitrary extra sections: list of (heading, body) tuples.
    # Rendered in order, after Usage, before License.
    # Future stack-specific content goes here until it earns its own field.
    sections: list[tuple[str, str]] = field(default_factory=list)

    # License identifier. If None and a pyproject.toml is present at root,
    # we attempt to read it from [project.license]. Falls back to "MIT".
    license: str | None = None


def _try_read_pyproject(root: Path) -> dict[str, Any]:
    p = root / "pyproject.toml"
    if p.exists():
        try:
            return tomllib.loads(p.read_text())
        except Exception:
            pass
    return {}


def _resolve_license(cfg: ReadmeConfig, pyproject: dict[str, Any]) -> str:
    if cfg.license is not None:
        return cfg.license
    # PEP 639: [project.license] = "MIT"
    # older: [project.license.text] = "MIT License"
    proj = pyproject.get("project", {})
    lic = proj.get("license")
    if isinstance(lic, str):
        return lic
    if isinstance(lic, dict):
        text = lic.get("text", "MIT")
        if isinstance(text, str):
            return text.split()[0]  # "MIT License" → "MIT"
        return "MIT"
    return "MIT"


def _code_block(lines: list[str], lang: str = "") -> str:
    if not lines:
        return ""
    body = "\n".join(lines)
    return f"```{lang}\n{body}\n```"


def render(cfg: ReadmeConfig, root: Path | None = None) -> str:
    """Return a rendered README string.

    Args:
        cfg: README configuration.
        root: Project root. When provided, used to read pyproject.toml for
              dynamic version/license resolution.
    """
    pyproject = _try_read_pyproject(root) if root is not None else {}
    resolved_license = _resolve_license(cfg, pyproject)

    parts: list[str] = []

    # Title + description
    parts.append(f"# {cfg.name}")
    if cfg.description:
        parts.append(f"\n{cfg.description}")

    # Install
    if cfg.install_commands:
        parts.append("\n## Install\n")
        parts.append(_code_block(cfg.install_commands, "bash"))

    # Usage
    if cfg.usage_commands:
        parts.append("\n## Usage\n")
        parts.append(_code_block(cfg.usage_commands, "bash"))

    # Extra sections
    for heading, body in cfg.sections:
        parts.append(f"\n## {heading}\n")
        parts.append(body.rstrip())

    # License
    parts.append(f"\n## License\n\n{resolved_license}")

    return "\n".join(parts) + "\n"


def write_readme(root: Path, cfg: ReadmeConfig) -> None:
    """Render and write README.md into root."""
    (root / "README.md").write_text(render(cfg, root=root))
