"""test requirements parser."""

from pathlib import Path

import pytest

from pybuild_deps.exceptions import PyBuildDepsError
from pybuild_deps.parsers import parse_requirements


def test_pinned_requirements(tmp_path, mocker):
    """Test parsing requirements with pinned dependencies."""
    requirements_path: Path = tmp_path / "requirements.txt"
    requirements_path.write_text("cryptography==40.0.0")
    requirements_list = list(parse_requirements(str(requirements_path), mocker.Mock()))
    assert [r.name for r in requirements_list] == ["cryptography"]


def test_unpinned_requirements(tmp_path, mocker):
    """Test parsing requirements with unpinned dependencies."""
    requirements_path: Path = tmp_path / "requirements.txt"
    requirements_path.write_text("cryptography>40")
    with pytest.raises(PyBuildDepsError):
        list(parse_requirements(str(requirements_path), mocker.Mock()))
