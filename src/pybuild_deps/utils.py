"""utilities module."""

from urllib.parse import urlparse

from pip._internal.req import InstallRequirement
from piptools.utils import is_pinned_requirement as _is_pinned_requirement

from pybuild_deps.exceptions import PyBuildDepsError


def get_version(ireq: InstallRequirement):
    """Get version string from InstallRequirement."""
    if not is_supported_requirement(ireq):
        raise PyBuildDepsError(f"requirement '{ireq}' is not exact.")
    if ireq.req.url:
        return ireq.req.url
    return next(iter(ireq.specifier)).version


def is_supported_requirement(ireq: InstallRequirement):
    """Returns True if requirement is pinned, vcs poiting to a SHA or a direct url."""
    return (
        _is_pinned_requirement(ireq) or _is_pinned_vcs(ireq) or _is_non_vcs_link(ireq)
    )


def _is_pinned_vcs(ireq: InstallRequirement):
    """Check if given ireq is a pinned vcs dependency."""
    if not ireq.link:
        return False
    if not ireq.link.is_vcs:
        return False
    parsed_url = urlparse(ireq.req.url)
    parts = len(parsed_url.path.split("@"))
    # pip supports pinned vcs urls pointing to a hash/branch/tag like
    # some_project.git@da39a3ee5e6b4b0d3255bfef95601890afd80709
    # https://pip.pypa.io/en/latest/topics/vcs-support/
    return parts == 2


def _is_non_vcs_link(ireq: InstallRequirement):
    if not ireq.link:
        return False
    return not ireq.link.is_vcs
