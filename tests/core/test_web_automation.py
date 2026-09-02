from unittest.mock import MagicMock, patch

import pytest

from automation.core.config import AutomationConfig
from automation.types.web.automation import WebAutomation


@pytest.fixture
def automation():
    config = AutomationConfig(
        id="test-automation",
        name="Test Automation",
        type="web",
        strategy="voting",
        config={
            "web": {
                "url": "https://example.com",
                "session_file": (
                    "sessions/test_session.json"
                ),
            },
            "strategy": {
                "action_delay_seconds": 3,
            },
        },
        state_file="state/test.json",
        log_file="logs/test.log",
        check_interval_seconds=60,
        enabled=True,
    )

    return WebAutomation(config)


# ============================================================
# is_started()
# ============================================================


def test_is_started_returns_false_before_start(
    automation,
):
    assert automation.is_started() is False


def test_is_started_returns_true_when_all_resources_exist(
    automation,
):
    automation.playwright = MagicMock()
    automation.browser = MagicMock()
    automation.context = MagicMock()
    automation.page = MagicMock()

    assert automation.is_started() is True


def test_is_started_returns_false_when_any_resource_is_missing(
    automation,
):
    automation.playwright = MagicMock()
    automation.browser = MagicMock()
    automation.context = MagicMock()
    automation.page = None

    assert automation.is_started() is False


# ============================================================
# start()
# ============================================================


@patch(
    "automation.types.web.automation.sync_playwright"
)
def test_start_creates_playwright_browser_context_and_page(
    mock_sync_playwright,
    automation,
):
    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()

    mock_sync_playwright.return_value.start.return_value = (
        playwright
    )

    playwright.chromium.launch.return_value = browser
    browser.new_context.return_value = context
    context.new_page.return_value = page

    automation.start()

    mock_sync_playwright.assert_called_once()

    mock_sync_playwright.return_value.start.assert_called_once()

    playwright.chromium.launch.assert_called_once_with(
        headless=True,
    )

    browser.new_context.assert_called_once_with()

    context.new_page.assert_called_once()

    assert automation.playwright is playwright
    assert automation.browser is browser
    assert automation.context is context
    assert automation.page is page

    page.goto.assert_not_called()


@patch(
    "automation.types.web.automation.sync_playwright"
)
def test_start_loads_storage_state_when_session_file_exists(
    mock_sync_playwright,
    automation,
    tmp_path,
):
    session_file = (
        tmp_path / "test_session.json"
    )

    session_file.write_text(
        "{}",
        encoding="utf-8",
    )

    automation.config = AutomationConfig(
        id=automation.config.id,
        name=automation.config.name,
        type=automation.config.type,
        strategy=automation.config.strategy,
        config={
            "web": {
                "url": automation.config.config[
                    "web"
                ]["url"],
                "session_file": str(
                    session_file
                ),
            },
            "strategy": {
                "action_delay_seconds": 3,
            },
        },
        state_file=automation.config.state_file,
        log_file=automation.config.log_file,
        check_interval_seconds=(
            automation.config.check_interval_seconds
        ),
        enabled=automation.config.enabled,
    )

    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()

    mock_sync_playwright.return_value.start.return_value = (
        playwright
    )

    playwright.chromium.launch.return_value = browser
    browser.new_context.return_value = context
    context.new_page.return_value = page

    automation.start()

    browser.new_context.assert_called_once_with(
        storage_state=str(session_file),
    )


@patch(
    "automation.types.web.automation.sync_playwright"
)
def test_start_does_not_load_storage_state_when_session_file_does_not_exist(
    mock_sync_playwright,
    automation,
    tmp_path,
):
    session_file = (
        tmp_path / "missing_session.json"
    )

    automation.config = AutomationConfig(
        id=automation.config.id,
        name=automation.config.name,
        type=automation.config.type,
        strategy=automation.config.strategy,
        config={
            "web": {
                "url": automation.config.config[
                    "web"
                ]["url"],
                "session_file": str(
                    session_file
                ),
            },
            "strategy": {
                "action_delay_seconds": 3,
            },
        },
        state_file=automation.config.state_file,
        log_file=automation.config.log_file,
        check_interval_seconds=(
            automation.config.check_interval_seconds
        ),
        enabled=automation.config.enabled,
    )

    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()

    mock_sync_playwright.return_value.start.return_value = (
        playwright
    )

    playwright.chromium.launch.return_value = browser
    browser.new_context.return_value = context
    context.new_page.return_value = page

    automation.start()

    browser.new_context.assert_called_once_with()


@patch(
    "automation.types.web.automation.sync_playwright"
)
def test_start_does_nothing_when_already_started(
    mock_sync_playwright,
    automation,
):
    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()

    automation.playwright = playwright
    automation.browser = browser
    automation.context = context
    automation.page = page

    automation.start()

    mock_sync_playwright.assert_not_called()

    playwright.chromium.launch.assert_not_called()
    browser.new_context.assert_not_called()
    context.new_page.assert_not_called()


# ============================================================
# close()
# ============================================================


def test_close_closes_context_browser_and_playwright(
    automation,
):
    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()

    automation.playwright = playwright
    automation.browser = browser
    automation.context = context
    automation.page = page

    automation.close()

    context.close.assert_called_once()
    browser.close.assert_called_once()
    playwright.stop.assert_called_once()

    assert automation.playwright is None
    assert automation.browser is None
    assert automation.context is None
    assert automation.page is None


def test_close_is_safe_when_not_started(
    automation,
):
    automation.close()

    assert automation.playwright is None
    assert automation.browser is None
    assert automation.context is None
    assert automation.page is None


def test_close_continues_cleanup_when_context_close_fails(
    automation,
):
    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()

    context.close.side_effect = Exception(
        "Context close failed"
    )

    automation.playwright = playwright
    automation.browser = browser
    automation.context = context
    automation.page = MagicMock()

    automation.close()

    context.close.assert_called_once()
    browser.close.assert_called_once()
    playwright.stop.assert_called_once()

    assert automation.playwright is None
    assert automation.browser is None
    assert automation.context is None
    assert automation.page is None


def test_close_continues_cleanup_when_browser_close_fails(
    automation,
):
    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()

    browser.close.side_effect = Exception(
        "Browser close failed"
    )

    automation.playwright = playwright
    automation.browser = browser
    automation.context = context
    automation.page = MagicMock()

    automation.close()

    context.close.assert_called_once()
    browser.close.assert_called_once()
    playwright.stop.assert_called_once()

    assert automation.playwright is None
    assert automation.browser is None
    assert automation.context is None
    assert automation.page is None


def test_close_continues_cleanup_when_playwright_stop_fails(
    automation,
):
    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()

    playwright.stop.side_effect = Exception(
        "Playwright stop failed"
    )

    automation.playwright = playwright
    automation.browser = browser
    automation.context = context
    automation.page = MagicMock()

    automation.close()

    context.close.assert_called_once()
    browser.close.assert_called_once()
    playwright.stop.assert_called_once()

    assert automation.playwright is None
    assert automation.browser is None
    assert automation.context is None
    assert automation.page is None


# ============================================================
# start() - failure paths
# ============================================================


@patch(
    "automation.types.web.automation.sync_playwright"
)
def test_start_raises_when_playwright_start_fails(
    mock_sync_playwright,
    automation,
):
    mock_sync_playwright.return_value.start.side_effect = (
        Exception("Playwright start failed")
    )

    with pytest.raises(
        Exception,
        match="Playwright start failed",
    ):
        automation.start()

    assert automation.browser is None
    assert automation.context is None
    assert automation.page is None


@patch(
    "automation.types.web.automation.sync_playwright"
)
def test_start_raises_when_browser_launch_fails(
    mock_sync_playwright,
    automation,
):
    playwright = MagicMock()

    mock_sync_playwright.return_value.start.return_value = (
        playwright
    )

    playwright.chromium.launch.side_effect = Exception(
        "Browser launch failed"
    )

    with pytest.raises(
        Exception,
        match="Browser launch failed",
    ):
        automation.start()

    assert automation.playwright is playwright
    assert automation.browser is None
    assert automation.context is None
    assert automation.page is None


@patch(
    "automation.types.web.automation.sync_playwright"
)
def test_start_raises_when_context_creation_fails(
    mock_sync_playwright,
    automation,
):
    playwright = MagicMock()
    browser = MagicMock()

    mock_sync_playwright.return_value.start.return_value = (
        playwright
    )

    playwright.chromium.launch.return_value = browser

    browser.new_context.side_effect = Exception(
        "Context creation failed"
    )

    with pytest.raises(
        Exception,
        match="Context creation failed",
    ):
        automation.start()

    assert automation.playwright is playwright
    assert automation.browser is browser
    assert automation.context is None
    assert automation.page is None


@patch(
    "automation.types.web.automation.sync_playwright"
)
def test_start_raises_when_page_creation_fails(
    mock_sync_playwright,
    automation,
):
    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()

    mock_sync_playwright.return_value.start.return_value = (
        playwright
    )

    playwright.chromium.launch.return_value = browser
    browser.new_context.return_value = context

    context.new_page.side_effect = Exception(
        "Page creation failed"
    )

    with pytest.raises(
        Exception,
        match="Page creation failed",
    ):
        automation.start()

    assert automation.playwright is playwright
    assert automation.browser is browser
    assert automation.context is context
    assert automation.page is None