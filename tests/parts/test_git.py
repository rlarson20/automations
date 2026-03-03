"""Tests for git module."""

from pathlib import Path


from automations_parts.git import (
    DEFAULT_GITIGNORE,
    write_gitignore,
)


def test_write_gitignore_default_content(tmp_project: Path) -> None:
    """Test write_gitignore() writes default patterns."""
    write_gitignore(tmp_project)

    gitignore = tmp_project / ".gitignore"
    assert gitignore.exists()

    content = gitignore.read_text()

    # Check for expected Python patterns
    assert "__pycache__/" in content
    assert "*.py[cod]" in content
    assert ".venv/" in content
    assert "dist/" in content
    assert "*.egg-info/" in content

    # Check for uv pattern
    assert "uv.lock" in content

    # Check for editor patterns
    assert ".idea/" in content
    assert ".vscode/" in content
    assert "*.swp" in content
    assert "*.swo" in content
    assert ".DS_Store" in content

    # Check for env patterns
    assert ".env" in content
    assert ".env.*" in content
    assert "!.env.example" in content


def test_write_gitignore_with_extra(tmp_project: Path) -> None:
    """Test write_gitignore() appends extra content."""
    extra = "\n# Custom\nbuild/\n*.log\n"

    write_gitignore(tmp_project, extra=extra)

    gitignore = tmp_project / ".gitignore"
    content = gitignore.read_text()

    # Default content should be present
    assert "__pycache__/" in content
    assert ".venv/" in content

    # Extra content should be appended
    assert "# Custom" in content
    assert "build/" in content
    assert "*.log" in content

    # Extra should come after default
    default_end = content.index("!.env.example")
    extra_start = content.index("# Custom")
    assert default_end < extra_start


def test_write_gitignore_extra_with_leading_trailing_whitespace(tmp_project: Path) -> None:
    """Test write_gitignore() handles extra with leading/trailing whitespace."""
    extra = "  \nbuild/\n  "

    write_gitignore(tmp_project, extra=extra)

    gitignore = tmp_project / ".gitignore"
    content = gitignore.read_text()

    # Should still have default content
    assert "__pycache__/" in content
    # Extra should be present without extra whitespace
    assert "build/" in content


def test_write_gitignore_creates_file(tmp_project: Path) -> None:
    """Test write_gitignore() creates .gitignore in correct location."""
    write_gitignore(tmp_project)

    gitignore = tmp_project / ".gitignore"
    assert gitignore.exists()
    assert gitignore.is_file()


def test_write_gitignore_empty_extra(tmp_project: Path) -> None:
    """Test write_gitignore() with empty extra string."""
    write_gitignore(tmp_project, extra="")

    gitignore = tmp_project / ".gitignore"
    content = gitignore.read_text()

    # Should just have default content
    assert content == DEFAULT_GITIGNORE


def test_write_gitignore_multiline_extra(tmp_project: Path) -> None:
    """Test write_gitignore() with multi-line extra content."""
    extra = "# My custom patterns\nnode_modules/\n*.log\ntemp/\n"

    write_gitignore(tmp_project, extra=extra)

    gitignore = tmp_project / ".gitignore"
    content = gitignore.read_text()

    assert "node_modules/" in content
    assert "*.log" in content
    assert "temp/" in content


def test_write_gitignore_preserves_default_format(tmp_project: Path) -> None:
    """Test that default content maintains expected format."""
    write_gitignore(tmp_project)

    gitignore = tmp_project / ".gitignore"
    content = gitignore.read_text()

    # Check that sections are properly formatted
    assert "# Python\n" in content
    assert "# uv\n" in content
    assert "# Editors\n" in content
    assert "# Env\n" in content


def test_write_gitignore_overwrites_existing(tmp_project: Path) -> None:
    """Test write_gitignore() overwrites existing file."""
    # Create an existing .gitignore
    gitignore = tmp_project / ".gitignore"
    gitignore.write_text("old content\n")

    write_gitignore(tmp_project, extra="new/")

    content = gitignore.read_text()

    # Should have new content, not old
    assert "old content" not in content
    assert "__pycache__/" in content  # from default
    assert "new/" in content  # from extra
