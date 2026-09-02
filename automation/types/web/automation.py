from pathlib import Path

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from automation.core.automation import Automation
from automation.core.config import AutomationConfig
from automation.types.web.config import WebAutomationConfig


class WebAutomation(Automation):
    def __init__(
        self,
        config: AutomationConfig,
    ):
        super().__init__(config)

        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    @property
    def web_config(self) -> WebAutomationConfig:
        return WebAutomationConfig(
            url=self.config.config["web"]["url"],
            session_file=self.config.config["web"]["session_file"],
        )

    def start(self) -> None:
        if self.is_started():
            return

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=True,
        )

        context_options = {}

        session_file = Path(
            self.web_config.session_file
        )

        if session_file.exists():
            context_options["storage_state"] = (
                str(session_file)
            )

        self.context = self.browser.new_context(
            **context_options,
        )

        self.page = self.context.new_page()

    def close(self) -> None:
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