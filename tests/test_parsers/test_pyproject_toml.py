"""Test pyproject toml parser."""

import pytest

from pybuild_deps.parsers import parse_pyproject_toml

EXAMPLE_TOML = """
[build-system]
requires = [
    "foo", # some comment
    "bar",
]

[tool.whatever]
some-data = "ble"
"""

EXAMPLE_TOML_WO_BUILD_SYSTEM = """
[tool.whatever]
some-data = "ble"
"""


@pytest.mark.parametrize(
    "toml,expected_result",
    [
        (EXAMPLE_TOML, ["foo", "bar"]),
        (EXAMPLE_TOML_WO_BUILD_SYSTEM, []),
    ],
)
def test_parse_toml(toml, expected_result):
    """Test parse pyproject.toml files."""
    assert parse_pyproject_toml(toml) == expected_result
