"""Parsers for PyBuild Deps."""

from configparser import ConfigParser

try:
    import tomllib as toml
except ImportError:
    import tomli as toml


from .setup_py import parse_setup_py  # imported here for convenience


def parse_pyproject_toml(content):
    """Parse build requirements from pyproject.toml files."""
    try:
        return toml.loads(content)["build-system"]["requires"]
    except KeyError:
        return []


def parse_setup_cfg(content):
    """Parse build requirements from setup.cfg files."""
    config = ConfigParser()
    config.read_string(content)
    try:
        build_requirements = config["options"]["setup_requires"]
    except KeyError:
        return []

    return [req.strip() for req in build_requirements.strip().splitlines()]
