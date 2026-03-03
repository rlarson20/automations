"""pyproject.toml read/patch/write helpers."""

from typing import Any

import tomllib
from pathlib import Path

import tomli_w


def read(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text())


def write(path: Path, data: dict[str, Any]) -> None:
    path.write_text(tomli_w.dumps(data))


def patch(path: Path, **updates: Any) -> None:
    """Shallow-merge updates into an existing pyproject.toml."""
    data = read(path)
    _deep_merge(data, updates)
    write(path, data)


def set_dependency_groups(path: Path, groups: dict[str, list[str] | list[dict[str, str]]]) -> None:
    """
    Set [dependency-groups] entries.
    groups: {"test": ["pytest", ...], "lint": [...], "dev": [{"include-group": "test"}, ...]}
    """
    data = read(path)
    data.setdefault("dependency-groups", {}).update(groups)
    write(path, data)


def _deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> None:
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
