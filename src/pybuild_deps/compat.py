"""compat module."""

# ruff:noqa: F401
try:
    import tomllib as toml
except ImportError:
    import tomli as toml
