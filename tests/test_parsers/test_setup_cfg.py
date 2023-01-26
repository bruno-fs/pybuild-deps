"""Test parsing build requirements from setup.cfg."""

import pytest

from pybuild_deps.parsers import parse_setup_cfg

EXAMPLE_CFG = """
[metadata]
name = foo

[options]
# comments are not supported inside keywords
setup_requires =
    foo
    bar
"""

EXAMPLE_CFG_WO_SETUP_REQUIRES = """
[metadata]
name = foo

[options]
install_requires =
    foo
    bar
"""


@pytest.mark.parametrize(
    "setup_cfg,expected_result",
    [(EXAMPLE_CFG, ["foo", "bar"]), (EXAMPLE_CFG_WO_SETUP_REQUIRES, [])],
)
def test_parse_setup_cfg(setup_cfg, expected_result):
    """Test parsing build requirements from setup.cfg."""
    assert parse_setup_cfg(setup_cfg) == expected_result
