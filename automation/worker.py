import json
import urllib.request

from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import (
    BrowserContext,
    Page,
    sync_playwright,
)

from automation.config import AutomationConfig
from automation.strategy import AutomationStrategy
from automation_state import save_state


BASE_DIR = Path(__file__).resolve().parent.parent

INTERNAL_STATE_URL = (
    "http://127.0.0.1:8000/api/internal/automation/state"
)


class AutomationWorker:
    def __init__(
        self,
        config: AutomationConfig,
        strategy: AutomationStrategy,
    ) -> None:
        self.config = config
        self.strategy = strategy

        self.session_file = (
            BASE_DIR / config.session_file
        )

        self.state_file = (
            BASE_DIR / config.state_file
        )

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        print(
            f"[{timestamp}] {message}",
            flush=True,
        )

    def publish_state(
        self,
        state: dict[str, Any],
    ) -> None:
        payload = json.dumps(
            state
        ).encode("utf-8")

        request = urllib.request.Request(
            INTERNAL_STATE_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=5,
            ) as response:

                if response.status != 200:
                    self.log(
                        "WARNING: state publish "
                        "returned "
                        f"HTTP {response.status}"
                    )

        except Exception as exc:
            self.log(
                "WARNING: failed to publish "
                f"state: {exc}"
            )

    def update_state(
        self,
        page: Page,
    ) -> dict[str, Any]:
        strategy_state = self.strategy.check(
            page
        )

        state = {
            "automationId": self.config.id,
            "automationName": self.config.name,
            "checkedAt": datetime.now().isoformat(),
            **strategy_state,
        }

        save_state(
            self.state_file,
            state,
        )

        self.publish_state(state)

        return state

    def find_available(
        self,
        page: Page,
    ) -> list[dict[str, Any]]:
        state = self.strategy.check(
            page
        )

        providers = state.get(
            "providers",
            [],
        )

        return [
            provider
            for provider in providers
            if provider.get(
                "available"
            ) is True
        ]

    def run_cycle(
        self,
        context: BrowserContext,
        page: Page,
    ) -> None:
        self.log(
            "Checking automation target..."
        )

        page.goto(
            self.config.url,
            wait_until="domcontentloaded",
        )

        state = self.update_state(
            page
        )

        self.log(
            f"Credits: {state.get('credits', '-')}"
            f" | Available: "
            f"{state.get('availableCount', '-')}"
        )

        while True:
            available = self.find_available(
                page
            )

            self.log(
                f"Available targets: "
                f"{len(available)}"
            )

            if not available:
                break

            target = available[0]

            success = self.strategy.execute(
                context,
                page,
                target,
            )

            self.update_state(
                page
            )

            if not success:
                self.log(
                    "Target execution was not "
                    "verified as successful."
                )

            import time

            time.sleep(
                self.config.action_delay_seconds
            )

    def run(self) -> None:
        if not self.session_file.exists():
            raise FileNotFoundError(
                "Session file not found: "
                f"{self.session_file}"
            )

        self.log(
            f"{self.config.name} worker starting..."
        )

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True
            )

            context = browser.new_context(
                storage_state=str(
                    self.session_file
                )
            )

            page = context.new_page()

            try:
                import time

                while True:
                    try:
                        self.run_cycle(
                            context,
                            page,
                        )

                        self.log(
                            "No more available "
                            "targets. Sleeping "
                            f"{self.config.check_interval_seconds}"
                            " seconds."
                        )

                        time.sleep(
                            self.config.check_interval_seconds
                        )

                    except Exception as exc:
                        self.log(
                            f"ERROR: "
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        )

                        self.log(
                            "Retrying in 5 minutes..."
                        )

                        time.sleep(300)

            finally:
                context.close()
                browser.close()