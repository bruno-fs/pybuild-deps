"""Test cases for the __main__ module."""

from os import chdir
from pathlib import Path

import pytest
from click.testing import CliRunner
from piptools.exceptions import PipToolsError
from piptools.repositories import PyPIRepository

from pybuild_deps import __main__ as main
from pybuild_deps.compile_build_dependencies import BuildDependencyCompiler
from pybuild_deps.constants import PIP_CACHE_DIR
from pybuild_deps.parsers import parse_requirements


@pytest.fixture
def pypi_repo():
    """PyPIRepository instance for testing."""
    return PyPIRepository([], cache_dir=PIP_CACHE_DIR)


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner(mix_stderr=False)


def test_main_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(main.cli)
    assert result.exit_code == 0


@pytest.mark.e2e
@pytest.mark.parametrize(
    "package_name,version,expected_deps",
    [
        ("urllib3", "1.26.13", []),
        (
            "cryptography",
            "39",
            [
                "setuptools>=40.6.0,!=60.9.0",
                "wheel",
                "cffi>=1.12; platform_python_implementation != 'PyPy'",
                "setuptools-rust>=0.11.4",
            ],
        ),
        (
            "cryptography",
            "git+https://github.com/pyca/cryptography@41.0.5",
            [
                "setuptools>=61.0.0",
                "wheel",
                "cffi>=1.12; platform_python_implementation != 'PyPy'",
                "setuptools-rust>=0.11.4",
            ],
        ),
    ],
)
def test_find_build_deps(
    cache: Path, runner: CliRunner, package_name, version, expected_deps
):
    """End to end testing for find-build-deps command."""
    assert not cache.exists()
    result = runner.invoke(main.cli, args=["find-build-deps", package_name, version])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == expected_deps
    assert cache.exists()
    # repeating the same test to cover a cached version
    result = runner.invoke(main.cli, args=["find-build-deps", package_name, version])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == expected_deps


@pytest.mark.parametrize(
    "package_name,version,expected_error",
    [
        (
            "tensorflow",
            "2.14.0",
            "PyPI doesn't have the source code for package tensorflow==2.14.0",
        ),
        (
            "grpcio",
            "1.59.0",
            "Unable to parse setup.py for package grpcio==1.59.0.",
        ),
        (
            "some-package",
            "git+https://example.com",
            "Unsupported requirement (some-package @ git+https://example.com). Url requirements must use a VCS scheme like 'git+https'.",  # noqa: E501
        ),
        (
            "cryptography",
            "git+https://github.com/pyca/cryptography",
            "Unsupported requirement (cryptography @ git+https://github.com/pyca/cryptography). Url requirements must use a VCS scheme like 'git+https'.",  # noqa: E501
        ),
    ],
)
def test_find_build_deps_error(
    cache: Path, runner: CliRunner, package_name, version, expected_error
):
    """End to end testing for find-build-deps command."""
    assert not cache.exists()
    result = runner.invoke(main.cli, args=["find-build-deps", package_name, version])
    assert result.exit_code == 2
    assert result.stderr.splitlines()[-1] == expected_error


@pytest.mark.e2e
def test_compile_greenpath(
    runner: CliRunner, tmp_path: Path, pypi_repo: PyPIRepository
):
    """Test happy path for compile command."""
    output = tmp_path / "requirements-build.txt"
    requirements_path: Path = tmp_path / "requirements.txt"
    requirements_path.write_text("cryptography==39.0.0")
    result = runner.invoke(
        main.cli, args=["compile", str(requirements_path), "-o", str(output)]
    )
    assert result.exit_code == 0
    expected_packages = {"setuptools-rust", "setuptools-scm"}
    build_requirements = list(parse_requirements(str(output), pypi_repo.session))
    assert expected_packages.issubset({r.name for r in build_requirements})


def test_compile_missing_requirements_txt(runner: CliRunner, tmp_path: Path):
    """Test compile without a requirements.txt."""
    chdir(tmp_path)
    result = runner.invoke(main.cli, args=["compile"])
    assert result.exit_code != 0
    err_message = result.stderr.splitlines()[-1]

    assert (
        err_message == "Error: Invalid value: Couldn't find a 'requirements.txt'."
        " You must specify at least one input file."
    )


@pytest.mark.e2e
@pytest.mark.parametrize("args", ["--no-header", "--generate-hashes", "-v", "-q"])
def test_compile_implicit_requirements_txt_and_non_default_options(
    runner: CliRunner,
    tmp_path: Path,
    cache: Path,
    args,
):
    """Exercise some options to ensure they are working."""
    chdir(tmp_path)
    requirements_path: Path = tmp_path / "requirements.txt"
    requirements_path.write_text("setuptools-rust==1.6.0")
    result = runner.invoke(main.cli, args=["compile", args])
    assert result.exit_code == 0
    assert {file.name for file in cache.glob("*")} == {"setuptools", "setuptools-rust"}


def test_compile_not_pinned_requirements_txt(runner: CliRunner, tmp_path: Path):
    """Ensure the appropriate error is thrown for non pinned requirements."""
    chdir(tmp_path)
    requirements_path: Path = tmp_path / "requirements.txt"
    requirements_path.write_text("setuptools-rust<1")
    result = runner.invoke(main.cli, args=["compile"])
    assert result.exit_code == 2
    assert (
        result.stderr.splitlines()[-1]
        == "requirement 'setuptools-rust<1 (from -r requirements.txt (line 1))' is not "
        "exact (pybuild-tools only supports pinned dependencies)."
    )


def test_compile_piptools_error(runner: CliRunner, tmp_path: Path, mocker):
    """Test error handling for exceptions raised by pip-tools."""
    mocker.patch.object(
        BuildDependencyCompiler, "resolve", side_effect=PipToolsError("SOME ERROR")
    )
    chdir(tmp_path)
    requirements_path: Path = tmp_path / "requirements.txt"
    requirements_path.write_text("setuptools-rust==1.6.0")
    result = runner.invoke(main.cli, args=["compile"])
    assert result.exit_code == 2
    assert result.stderr.splitlines()[-1] == "SOME ERROR"


def test_compile_unsolvable_dependencies(runner: CliRunner, tmp_path: Path, mocker):
    """Test error handling for exceptions raised by pip-tools."""
    chdir(tmp_path)
    requirements = ["foo==0.1.2"]
    requirements_path: Path = tmp_path / "requirements.txt"
    requirements_path.write_text("\n".join(requirements))
    outfile = tmp_path / "outfile"
    mocker.patch(
        "pybuild_deps.compile_build_dependencies.find_build_dependencies",
        return_value=["bar>=42", "bar<42"],
    )
    result = runner.invoke(main.cli, args=["compile", "-o", str(outfile)])
    assert result.exit_code == 2
    assert (
        "Impossible resolve dependencies. See the conflicting dependencies "
        "below:\nbar>=42 (from foo)\nbar<42 (from foo)" in result.stderr
    )
