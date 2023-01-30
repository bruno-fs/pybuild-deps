"""Get source code for a given package."""

import logging
from pathlib import Path

import requests
from xdg import xdg_cache_home

CACHE_PATH = xdg_cache_home() / "pybuild-deps"


def get_package_source(package_name: str, version: str) -> Path:
    """Get ource code for a given package."""
    cached_path = CACHE_PATH / package_name / version
    tarball_path = cached_path / "source.tar.gz"
    error_path = cached_path / "error.json"
    if tarball_path.exists():
        logging.info("using cached version for package %s==%s", package_name, version)
        return tarball_path

    elif error_path.exists():
        raise NotImplementedError()

    return retrieve_and_save_source_from_pypi(
        package_name, version, tarball_path=tarball_path, error_path=error_path
    )


def retrieve_and_save_source_from_pypi(
    package_name: str,
    version: str,
    *,
    tarball_path: Path,
    error_path: Path,
):
    """Retrieve package source from pypi and store it in a cache."""
    source_url = get_source_url(package_name, version)
    response = requests.get(source_url, timeout=10)
    if not response.ok:
        raise NotImplementedError()
    tarball_path.parent.mkdir(parents=True, exist_ok=True)
    tarball_path.write_bytes(response.content)
    return tarball_path


def get_source_url(package_name, version):
    """Get url for source code."""
    response = requests.get(
        f"https://pypi.org/pypi/{package_name}/{version}/json", timeout=10
    )
    if not response.ok:
        raise NotImplementedError()
    for url in response.json()["urls"]:  # pragma: no branch
        if url["python_version"] == "source":
            return url["url"]
