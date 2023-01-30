"""pytest configuration."""


def pytest_configure(config):
    """Configure pytst session."""
    config.addinivalue_line("markers", "e2e: end to end tests.")
