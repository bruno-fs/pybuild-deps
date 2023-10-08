"""pytest configuration."""


import pytest


def pytest_configure(config):
    """Configure pytst session."""
    config.addinivalue_line("markers", "e2e: end to end tests.")


@pytest.fixture
def cache(mocker, tmp_path):
    """Mock pybuild-deps cache."""
    mocked_cache = tmp_path / "cache"
    mocker.patch("pybuild_deps.constants.CACHE_PATH", mocked_cache)
    mocker.patch("pybuild_deps.source.CACHE_PATH", mocked_cache)
    yield mocked_cache
