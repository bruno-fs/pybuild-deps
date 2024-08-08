"""constants for pybuild deps."""

from xdg import xdg_cache_home


CACHE_PATH = xdg_cache_home() / "pybuild-deps"
PIP_CACHE_DIR = CACHE_PATH / "pip"
