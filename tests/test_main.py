"""Test cases for the __main__ module."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from pybuild_deps import __main__


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


@pytest.fixture
def cache(monkeypatch, tmp_path):
    """Mock pybuild-deps cache."""
    mocked_cache = tmp_path / "cache"
    monkeypatch.setattr("pybuild_deps.get_package_source.CACHE_PATH", mocked_cache)
    yield mocked_cache


def test_main_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(__main__.cli)
    assert result.exit_code == 0


def test_log_level(runner: CliRunner, mocker):
    """Test setting log level."""
    patched_logconfig = mocker.patch(
        "pybuild_deps.__main__.logging.basicConfig", side_effect=RuntimeError("STOP!!!")
    )
    result = runner.invoke(
        __main__.cli, ["--log-level", "INFO", "find-build-deps", "a", "b"]
    )
    assert result.exit_code == 1
    assert isinstance(result.exception, RuntimeError)
    assert patched_logconfig.call_args == mocker.call(level="INFO")


@pytest.mark.e2e
@pytest.mark.parametrize(
    "package_name,version,expected_deps",
    [
        ("urllib3", "1.26.13", []),
        (
            "cryptography",
            "39.0.0",
            [
                "setuptools>=40.6.0,!=60.9.0",
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
    result = runner.invoke(__main__.find_build_deps, args=[package_name, version])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == expected_deps
    assert cache.exists()
    # repeating the same test to cover a cached version
    result = runner.invoke(__main__.find_build_deps, args=[package_name, version])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == expected_deps
