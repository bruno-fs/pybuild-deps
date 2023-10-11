"""test compile_build_dependencies module."""

import logging

import pytest
from pip._internal.req.constructors import install_req_from_req_string
from piptools.repositories import PyPIRepository

from pybuild_deps.compile_build_dependencies import BuildDependencyCompiler
from pybuild_deps.constants import PIP_CACHE_DIR
from pybuild_deps.exceptions import PyBuildDepsError


@pytest.fixture
def compiler() -> BuildDependencyCompiler:
    """BuildDependencyCompiler instance."""
    repo = PyPIRepository([], cache_dir=PIP_CACHE_DIR)
    return BuildDependencyCompiler(repo)


def test_compile_greenpath(compiler):
    """Test compiling build dependencies happy path."""
    ireq = install_req_from_req_string("cryptography==40.0.0")
    dependencies = compiler.resolve([ireq])
    deps_per_name = {req.name: req for req in dependencies}
    assert {"setuptools-rust", "setuptools-scm"}.issubset(deps_per_name.keys())
    assert deps_per_name["setuptools-rust"].comes_from == "cryptography"
    assert deps_per_name["setuptools-scm"].comes_from == "setuptools-rust"


def test_unpinned_dependency(compiler):
    """Ensure unpinned dependencies will raise the appropriate error."""
    ireq = install_req_from_req_string("cryptography<40")
    with pytest.raises(PyBuildDepsError):
        compiler.resolve([ireq])


def test_dependency_with_complex_setup_py(compiler, caplog):
    """Ensure unparseable setup.py won't get in the way."""
    caplog.set_level(logging.ERROR)
    ireq = install_req_from_req_string("grpcio==1.59.0")
    compiler.resolve([ireq])
    assert caplog.messages[-1] == "Unable to parse setup.py for package grpcio==1.59.0."
