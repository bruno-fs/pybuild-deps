"""utilities module."""

from pip._internal.req import InstallRequirement
from piptools.utils import is_pinned_requirement

from pybuild_deps.exceptions import PyBuildDepsError


def get_version(ireq: InstallRequirement):
    """Get version string from InstallRequirement."""
    if not is_pinned_requirement(ireq):
        raise PyBuildDepsError(
            f"requirement '{ireq}' is not exact "
            "(pybuild-tools only supports pinned dependencies)."
        )
    return next(iter(ireq.specifier)).version
