from pathlib import Path

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from automation.core.config import AutomationConfig


class WebAutomation:
    """
    Web-based automation environment.

    Responsible for:
    - Starting Playwright
    - Launching the browser
    - Creating the browser context
    - Loading the configured session
    - Opening the configured URL
    - Providing the page to the strategy
    - Cleaning up browser resources
    """

    def __init__(
        self,
        config: AutomationConfig,
    ):
        self.config = config

        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def start(self) -> None:
        """
        Start the Playwright browser and open the configured URL.
        """

        if self.playwright is not None:
            return

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=False,
        )

        session_file = Path(
            self.config.session_file
        )

        context_options = {}

        if session_file.exists():
            context_options["storage_state"] = str(
                session_file
            )

        self.context = self.browser.new_context(
            **context_options
        )

        self.page = self.context.new_page()

        self.page.goto(
            self.config.url,
            wait_until="domcontentloaded",
        )

    def close(self) -> None:
        """
        Close the browser and Playwright resources.
        """

        if self.context is not None:
            try:
                self.context.close()
            except Exception:
                pass

        if self.browser is not None:
            try:
                self.browser.close()
            except Exception:
                pass

        if self.playwright is not None:
            try:
                self.playwright.stop()
            except Exception:
                pass

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    def is_started(self) -> bool:
        return (
            self.playwright is not None
            and self.browser is not None
            and self.context is not None
            and self.page is not None
        )