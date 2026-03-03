"""Tests for readme module."""

from pathlib import Path


from automations_parts.readme import (
    ReadmeConfig,
    render,
    write_readme,
    _code_block,
    _resolve_license,
    _try_read_pyproject,
)


def test_render_minimal() -> None:
    """Test render() with only required fields."""
    cfg = ReadmeConfig(name="my-project")

    result = render(cfg)

    assert result == "# my-project\n\n## License\n\nMIT\n"


def test_render_with_description() -> None:
    """Test render() with description."""
    cfg = ReadmeConfig(
        name="my-project",
        description="Does the thing.",
    )

    result = render(cfg)

    assert result == "# my-project\n\nDoes the thing.\n\n## License\n\nMIT\n"


def test_render_with_install_commands() -> None:
    """Test render() with install commands."""
    cfg = ReadmeConfig(
        name="my-project",
        install_commands=["uv sync", "uv run pytest"],
    )

    result = render(cfg)

    assert "## Install" in result
    assert "```bash" in result
    assert "uv sync" in result
    assert "uv run pytest" in result


def test_render_with_usage_commands() -> None:
    """Test render() with usage commands."""
    cfg = ReadmeConfig(
        name="my-project",
        usage_commands=["uv run my_app"],
    )

    result = render(cfg)

    assert "## Usage" in result
    assert "```bash" in result
    assert "uv run my_app" in result


def test_render_with_all_fields() -> None:
    """Test render() with all standard fields."""
    cfg = ReadmeConfig(
        name="my-project",
        description="Does the thing.",
        install_commands=["uv sync"],
        usage_commands=["uv run app"],
    )

    result = render(cfg)

    lines = result.strip().split("\n")
    assert lines[0] == "# my-project"
    assert lines[2] == "Does the thing."
    assert "## Install" in result
    assert "## Usage" in result
    assert "## License" in result

    # Check order: title, description, install, usage, license
    install_idx = result.index("## Install")
    usage_idx = result.index("## Usage")
    license_idx = result.index("## License")
    assert install_idx < usage_idx < license_idx


def test_render_with_sections() -> None:
    """Test render() with extra sections."""
    cfg = ReadmeConfig(
        name="my-project",
        usage_commands=["uv run app"],
        sections=[
            ("Development", "Run tests with `uv run pytest`."),
            ("Contributing", "PRs welcome!"),
        ],
    )

    result = render(cfg)

    assert "## Development" in result
    assert "Run tests with `uv run pytest`." in result
    assert "## Contributing" in result
    assert "PRs welcome!" in result

    # Sections appear after Usage, before License
    usage_idx = result.index("## Usage")
    dev_idx = result.index("## Development")
    license_idx = result.index("## License")
    assert usage_idx < dev_idx < license_idx


def test_code_block_with_lines() -> None:
    """Test _code_block() with lines."""
    result = _code_block(["line 1", "line 2"], "bash")

    assert result == "```bash\nline 1\nline 2\n```"


def test_code_block_empty() -> None:
    """Test _code_block() with empty list."""
    result = _code_block([])

    assert result == ""


def test_code_block_no_lang() -> None:
    """Test _code_block() without language."""
    result = _code_block(["text"])

    assert result == "```\ntext\n```"


def test_resolve_license_explicit() -> None:
    """Test _resolve_license() with explicit license."""
    cfg = ReadmeConfig(name="test", license="Apache-2.0")
    pyproject = {}

    result = _resolve_license(cfg, pyproject)

    assert result == "Apache-2.0"


def test_resolve_license_from_pyproject_string() -> None:
    """Test _resolve_license() from PEP 639 string format."""
    cfg = ReadmeConfig(name="test", license=None)
    pyproject = {"project": {"license": "MIT"}}

    result = _resolve_license(cfg, pyproject)

    assert result == "MIT"


def test_resolve_license_from_pyproject_dict() -> None:
    """Test _resolve_license() from legacy dict format."""
    cfg = ReadmeConfig(name="test", license=None)
    pyproject = {"project": {"license": {"text": "MIT License"}}}

    result = _resolve_license(cfg, pyproject)

    assert result == "MIT"  # Extracts first word


def test_resolve_license_from_pyproject_dict_full_phrase() -> None:
    """Test _resolve_license() extracts first word from dict."""
    cfg = ReadmeConfig(name="test", license=None)
    pyproject = {"project": {"license": {"text": "Apache License 2.0"}}}

    result = _resolve_license(cfg, pyproject)

    assert result == "Apache"


def test_resolve_license_fallback() -> None:
    """Test _resolve_license() falls back to MIT."""
    cfg = ReadmeConfig(name="test", license=None)
    pyproject = {}

    result = _resolve_license(cfg, pyproject)

    assert result == "MIT"


def test_try_read_pyproject_missing(tmp_project: Path) -> None:
    """Test _try_read_pyproject() with missing file."""
    result = _try_read_pyproject(tmp_project)

    assert result == {}


def test_try_read_pyproject_valid(tmp_project: Path) -> None:
    """Test _try_read_pyproject() with valid file."""
    pyproject = tmp_project / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test"')

    result = _try_read_pyproject(tmp_project)

    assert result == {"project": {"name": "test"}}


def test_try_read_pyproject_invalid(tmp_project: Path) -> None:
    """Test _try_read_pyproject() with invalid TOML returns empty dict."""
    pyproject = tmp_project / "pyproject.toml"
    pyproject.write_text("invalid [toml")

    result = _try_read_pyproject(tmp_project)

    assert result == {}


def test_write_readme(tmp_project: Path) -> None:
    """Test write_readme() creates file with correct content."""
    cfg = ReadmeConfig(
        name="test-project",
        description="A test project.",
    )

    write_readme(tmp_project, cfg)

    readme = tmp_project / "README.md"
    assert readme.exists()

    content = readme.read_text()
    assert "# test-project" in content
    assert "A test project." in content
    assert "## License\n\nMIT" in content


def test_render_with_root_reads_pyproject(tmp_project: Path) -> None:
    """Test render() reads license from pyproject when root is provided."""
    pyproject = tmp_project / "pyproject.toml"
    pyproject.write_text('[project]\nlicense = "Apache-2.0"')

    cfg = ReadmeConfig(name="test")
    result = render(cfg, root=tmp_project)

    assert "## License\n\nApache-2.0" in result


def test_render_with_root_missing_pyproject(tmp_project: Path) -> None:
    """Test render() falls back to default when pyproject missing."""
    cfg = ReadmeConfig(name="test")
    result = render(cfg, root=tmp_project)

    assert "## License\n\nMIT" in result
