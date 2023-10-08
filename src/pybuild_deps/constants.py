"""constants for pybuild deps."""

from pip._internal.utils.appdirs import user_cache_dir
from xdg import xdg_cache_home

CACHE_PATH = xdg_cache_home() / "pybuild-deps"
PIP_CACHE_DIR = user_cache_dir("pybuild-deps")
