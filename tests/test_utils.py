"""test utils module."""

import pytest
from pip._internal.req.constructors import install_req_from_req_string

from pybuild_deps.utils import get_version, is_pinned_requirement


@pytest.mark.parametrize(
    "req",
    [
        "requests==X.Y.Z",
        "requests @ git+https://github.com/psf/requests@some-commit-sha",
    ],
)
def test_is_pinned_or_vcs(req):
    """Ensure pinned or vcs dependencies are properly detected."""
    ireq = install_req_from_req_string(req)
    assert is_pinned_requirement(ireq)


@pytest.mark.parametrize(
    "req",
    [
        "requests>X.Y.Z",
        "requests @ git+https://github.com/psf/requests",
        "requests @ https://example.com",
        "requests @ https://github.com/psf/requests@some-commit-sha",
        "requests",
    ],
)
def test_not_pinned_or_vcs(req):
    """Negative test for 'is_pinned_or_vcs'."""
    ireq = install_req_from_req_string(req)
    assert not is_pinned_requirement(ireq)


def test_get_version_url():
    """Check get version for vcs dependencies."""
    ireq = install_req_from_req_string(
        "some-package @ git+https://remote.url/some_project@commitsha"
    )
    version = get_version(ireq)
    assert version == "git+https://remote.url/some_project@commitsha"
