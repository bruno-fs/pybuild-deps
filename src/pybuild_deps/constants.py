"""constants for pybuild deps."""

from piptools.locations import CACHE_DIR as PIPTOOLS_CACHE_DIR  # noqa: F401
from xdg import xdg_cache_home


CACHE_PATH = xdg_cache_home() / "pybuild-deps"
