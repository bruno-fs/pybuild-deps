"""utilities module."""

from urllib.parse import urlparse

from pip._internal.req import InstallRequirement
from piptools.utils import is_pinned_requirement as _is_pinned_requirement

from pybuild_deps.exceptions import PyBuildDepsError


def get_version(ireq: InstallRequirement):
    """Get version string from InstallRequirement."""
    if not is_pinned_requirement(ireq):
        raise PyBuildDepsError(
            f"requirement '{ireq}' is not exact "
            "(pybuild-tools only supports pinned dependencies)."
        )
    if ireq.link and ireq.link.is_vcs:
        return ireq.req.url
    return next(iter(ireq.specifier)).version


def is_pinned_requirement(ireq: InstallRequirement):
    """Returns True if requirement is pinned or vcs."""
    return _is_pinned_requirement(ireq) or is_pinned_vcs(ireq)


def is_pinned_vcs(ireq: InstallRequirement):
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
