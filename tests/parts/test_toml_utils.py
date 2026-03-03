"""Tests for toml_utils module."""

from pathlib import Path

import pytest

from automations_parts.toml_utils import (
    _deep_merge,
    patch,
    read,
    set_dependency_groups,
    write,
)


def test_read_write_roundtrip(tmp_project: Path) -> None:
    """Test that write() followed by read() preserves data."""
    pyproject = tmp_project / "pyproject.toml"
    data = {
        "project": {"name": "test-project", "version": "0.1.0"},
        "dependency-groups": {"test": ["pytest"]},
    }

    write(pyproject, data)
    result = read(pyproject)

    assert result == data


def test_read_missing_file(tmp_project: Path) -> None:
    """Test that read() raises FileNotFoundError for missing files."""
    pyproject = tmp_project / "nonexistent.toml"

    with pytest.raises(FileNotFoundError):
        read(pyproject)


def test_write_creates_file(tmp_project: Path) -> None:
    """Test that write() creates the file."""
    pyproject = tmp_project / "pyproject.toml"
    data = {"project": {"name": "test"}}

    write(pyproject, data)

    assert pyproject.exists()
    assert 'name = "test"' in pyproject.read_text()


def test_patch_shallow_merge(tmp_project: Path) -> None:
    """Test that patch() shallow-merges updates into existing file."""
    pyproject = tmp_project / "pyproject.toml"
    original = {
        "project": {"name": "test", "version": "0.1.0"},
        "build-system": {"requires": ["hatchling"]},
    }
    write(pyproject, original)

    patch(pyproject, project={"description": "New description"})

    result = read(pyproject)
    assert result["project"]["name"] == "test"  # preserved
    assert result["project"]["description"] == "New description"  # added
    assert result["project"]["version"] == "0.1.0"  # preserved
    assert result["build-system"]["requires"] == ["hatchling"]  # preserved


def test_patch_deep_merge(tmp_project: Path) -> None:
    """Test that patch() deep-merges nested dicts."""
    pyproject = tmp_project / "pyproject.toml"
    original = {
        "project": {"name": "test", "dependencies": ["rich"]},
        "tool": {"ruff": {"line-length": 100}},
    }
    write(pyproject, original)

    patch(
        pyproject,
        project={"dependencies": ["tomli"]},  # replaces list
        tool={"ruff": {"target-version": "py312"}},  # merges into nested dict
    )

    result = read(pyproject)
    assert result["project"]["dependencies"] == ["tomli"]  # replaced
    assert result["tool"]["ruff"]["line-length"] == 100  # preserved
    assert result["tool"]["ruff"]["target-version"] == "py312"  # added


def test_patch_raises_if_missing(tmp_project: Path) -> None:
    """Test that patch() raises FileNotFoundError if file doesn't exist."""
    pyproject = tmp_project / "pyproject.toml"

    with pytest.raises(FileNotFoundError):
        patch(pyproject, project={"name": "test"})


def test_set_dependency_groups_fresh_file(tmp_project: Path) -> None:
    """Test set_dependency_groups() on a new pyproject.toml."""
    pyproject = tmp_project / "pyproject.toml"
    write(pyproject, {"project": {"name": "test"}})

    set_dependency_groups(
        pyproject,
        {
            "test": ["pytest", "pytest-mock"],
            "lint": ["ruff", "mypy"],
        },
    )

    result = read(pyproject)
    assert result["dependency-groups"]["test"] == ["pytest", "pytest-mock"]
    assert result["dependency-groups"]["lint"] == ["ruff", "mypy"]


def test_set_dependency_groups_preserves_existing(tmp_project: Path) -> None:
    """Test that set_dependency_groups() preserves existing groups."""
    pyproject = tmp_project / "pyproject.toml"
    write(
        pyproject,
        {
            "project": {"name": "test"},
            "dependency-groups": {
                "test": ["pytest"],
                "dev": [{"include-group": "test"}],
            },
        },
    )

    set_dependency_groups(
        pyproject,
        {"lint": ["ruff", "mypy"]},
    )

    result = read(pyproject)
    assert result["dependency-groups"]["test"] == ["pytest"]  # preserved
    assert result["dependency-groups"]["dev"] == [{"include-group": "test"}]  # preserved
    assert result["dependency-groups"]["lint"] == ["ruff", "mypy"]  # added


def test_set_dependency_groups_creates_section(tmp_project: Path) -> None:
    """Test set_dependency_groups() when dependency-groups doesn't exist."""
    pyproject = tmp_project / "pyproject.toml"
    write(pyproject, {"project": {"name": "test"}})

    set_dependency_groups(
        pyproject,
        {"test": ["pytest"]},
    )

    result = read(pyproject)
    assert "dependency-groups" in result
    assert result["dependency-groups"]["test"] == ["pytest"]


def test_deep_merge_dict_into_dict() -> None:
    """Test _deep_merge() with two dicts."""
    base = {"a": 1, "b": {"x": 10, "y": 20}}
    overrides = {"b": {"y": 200, "z": 30}, "c": 3}

    _deep_merge(base, overrides)

    assert base == {"a": 1, "b": {"x": 10, "y": 200, "z": 30}, "c": 3}


def test_deep_merge_non_dict_overrides() -> None:
    """Test _deep_merge() when override value is not a dict."""
    base = {"a": {"x": 1}, "b": [1, 2, 3]}
    overrides = {"a": "new value", "b": [4, 5]}

    _deep_merge(base, overrides)

    assert base == {"a": "new value", "b": [4, 5]}


def test_deep_merge_empty_overrides() -> None:
    """Test _deep_merge() with empty overrides."""
    base = {"a": 1, "b": 2}

    _deep_merge(base, {})

    assert base == {"a": 1, "b": 2}
