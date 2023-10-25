"""Get source code for a given package."""

import logging
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

import requests
from pip._internal.operations.prepare import unpack_vcs_link
from pip._internal.req.constructors import install_req_from_req_string

from pybuild_deps.constants import CACHE_PATH
from pybuild_deps.exceptions import PyBuildDepsError
from pybuild_deps.utils import is_pinned_vcs


def get_package_source(package_name: str, version: str) -> Path:
    """Get source code for a given package."""
    parsed_url = urlparse(version)
    is_url = all((parsed_url.scheme, parsed_url.netloc))

    if is_url:
        if parsed_url.path:
            path = parsed_url.path[1:]
        else:
            path = ""
        cached_path = (
            CACHE_PATH / package_name / parsed_url.scheme / parsed_url.netloc / path
        )
    else:
        cached_path = CACHE_PATH / package_name / version
    tarball_path = cached_path / "source.tar.gz"
    error_path = cached_path / "error.json"
    if tarball_path.exists():
        logging.info("using cached version for package %s==%s", package_name, version)
        return tarball_path

    elif error_path.exists():
        raise NotImplementedError()

    if is_url:
        # assume url is pointing to VCS - if it's not an error will be thrown later
        return retrieve_and_save_source_from_vcs(
            package_name, version, tarball_path=tarball_path, error_path=error_path
        )

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
    source_url = get_source_url_from_pypi(package_name, version)
    response = requests.get(source_url, timeout=10)
    response.raise_for_status()
    tarball_path.parent.mkdir(parents=True, exist_ok=True)
    tarball_path.write_bytes(response.content)
    return tarball_path


def retrieve_and_save_source_from_vcs(
    package_name: str,
    version: str,
    *,
    tarball_path: Path,
    error_path: Path,
):
    """Retrieve package source from VCS."""
    ireq = install_req_from_req_string(f"{package_name} @ {version}")
    if not is_pinned_vcs(ireq):
        raise PyBuildDepsError(
            f"Unsupported requirement ({ireq.name} @ {ireq.link}). Url requirements "
            "must use a VCS scheme like 'git+https'."
        )
    tarball_path.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as tmp_dir, tarfile.open(tarball_path, "w") as tarball:
        unpack_vcs_link(ireq.link, tmp_dir, verbosity=0)
        tarball.add(tmp_dir, arcname=package_name)
    return tarball_path


def get_source_url_from_pypi(package_name, version):
    """Get url for source code for a given package on pypi."""
    response = requests.get(
        f"https://pypi.org/pypi/{package_name}/{version}/json", timeout=10
    )
    response.raise_for_status()
    for url in response.json()["urls"]:  # pragma: no branch
        if url["python_version"] == "source":
            return url["url"]
    raise PyBuildDepsError(
        f"PyPI doesn't have the source code for package {package_name}=={version}"
    )
