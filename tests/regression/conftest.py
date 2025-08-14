"""Configuration for regression tests."""

import pytest


def pytest_configure(config):
    """Configure pytest for regression tests."""
    # Add markers for playwright tests
    config.addinivalue_line(
        "markers", "playwright: marks tests as requiring playwright (deselect with '-m \"not playwright\"')"
    )


@pytest.fixture(scope="session")
def playwright_browser():
    """Session-scoped playwright browser fixture."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("Playwright not available")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def browser_page(playwright_browser):
    """Page fixture for playwright tests."""
    context = playwright_browser.new_context()
    page = context.new_page()
    yield page
    context.close()
