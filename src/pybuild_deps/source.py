"""Get source code for a given package."""

from __future__ import annotations

import logging
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory

from pip._internal.exceptions import InstallationError
from pip._internal.network.download import Downloader
from pip._internal.network.session import PipSession
from pip._internal.operations.prepare import unpack_url
from pip._internal.req import InstallRequirement
from pip._internal.utils.temp_dir import global_tempdir_manager

from pybuild_deps.constants import CACHE_PATH
from pybuild_deps.exceptions import PyBuildDepsError
from pybuild_deps.utils import get_version, is_supported_requirement


def get_package_source(
    ireq: InstallRequirement, pip_session: PipSession | None = None
) -> Path:
    """Get source code for a given package."""
    version = get_version(ireq)
    package_name = ireq.name
    cached_path = CACHE_PATH / package_name / version
    tarball_path = cached_path / "source.tar.gz"
    error_path = cached_path / "error.json"
    if tarball_path.exists():
        logging.info("using cached version for package %s==%s", package_name, version)
        return tarball_path

    elif error_path.exists():
        raise NotImplementedError()

    return retrieve_and_save_source_from_url(
        ireq,
        tarball_path=tarball_path,
        error_path=error_path,
        pip_session=pip_session,
    )


def retrieve_and_save_source_from_url(
    ireq: InstallRequirement,
    *,
    tarball_path: Path,
    error_path: Path,
    pip_session: PipSession = None,
):
    """Retrieve package source from URL."""
    if not is_supported_requirement(ireq):
        raise PyBuildDepsError(
            f"Unsupported requirement '{ireq.req}'. Requirement must be either pinned "
            "(==), a vcs link with sha or a direct url."
        )

    pip_session = pip_session or PipSession()
    pip_downloader = Downloader(pip_session, "")

    with global_tempdir_manager(), TemporaryDirectory() as tmp_dir:
        try:
            unpack_url(
                ireq.req.url,
                tmp_dir,
                download=pip_downloader,
                verbosity=0,
            )
        except InstallationError as err:
            raise PyBuildDepsError(
                f"Unable to unpack '{ireq.req}'. Is '{ireq.link}' a python package?"
            ) from err
        tarball_path.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tarball_path, "w:gz") as tarball:
            tarball.add(tmp_dir, arcname=ireq.name)
    return tarball_path
