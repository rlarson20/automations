"""Shared fixtures for automations tests."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Return a temp directory suitable as a fake project root."""
    return tmp_path
