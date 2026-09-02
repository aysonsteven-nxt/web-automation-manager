from pathlib import Path
from typing import Any

import requests

from automation.core.config import AutomationConfig
from automation.core.factory import AutomationFactory
from automation.core.state import save_state
from automation.types.web.automation import WebAutomation


class AutomationWorker:
    """
    Executes a configured automation.

    The worker is responsible for:
    - Creating the automation strategy
    - Creating the automation type
    - Running the automation lifecycle
    - Saving automation state
    - Publishing automation state

    Domain-specific behavior belongs to the strategy.
    """

    INTERNAL_STATE_URL = (
        "http://127.0.0.1:8000"
        "/api/internal/automation/state"
    )

    def __init__(
        self,
        config: AutomationConfig,
    ):
        self.config = config
        self.strategy = AutomationFactory.create_strategy(
            config.type,
            config.strategy,
        )

        self.automation = None

    def run(self) -> None:
        """
        Start and execute the automation.
        """

        print(
            f"Starting automation: "
            f"{self.config.name}",
            flush=True,
        )

        try:
            self.automation = self._create_automation()

            self.automation.start()

            self._execute()

        except Exception as exc:
            print(
                f"Automation '{self.config.id}' "
                f"failed: {exc}",
                flush=True,
            )
            raise

        finally:
            if self.automation is not None:
                self.automation.close()

            print(
                f"Automation stopped: "
                f"{self.config.name}",
                flush=True,
            )

    def _create_automation(self):
        """
        Create the concrete automation type.

        Currently supported:
        - web
        """

        if self.config.type == "web":
            return WebAutomation(
                self.config
            )

        raise ValueError(
            f"Unsupported automation type: "
            f"'{self.config.type}'"
        )

    def _execute(self) -> None:
        """
        Execute the strategy and periodically check
        the automation state.
        """

        if self.automation is None:
            raise RuntimeError(
                "Automation has not been started."
            )

        state = self.strategy.check(
            self.automation
        )

        self._save_and_publish_state(
            state
        )

        print(
            f"Automation '{self.config.id}' "
            f"state checked.",
            flush=True,
        )

        while True:
            state = self.strategy.check(
                self.automation
            )

            self._save_and_publish_state(
                state
            )

            targets = [
                target
                for target in state.get(
                    "providers",
                    [],
                )
                if target.get(
                    "available",
                    False,
                )
            ]

            for target in targets:
                try:
                    success = self.strategy.execute(
                        self.automation,
                        target,
                    )

                    if success:
                        print(
                            f"Automation "
                            f"'{self.config.id}': "
                            f"target {target.get('id')} "
                            f"executed successfully.",
                            flush=True,
                        )

                        state = self.strategy.check(
                            self.automation
                        )

                        self._save_and_publish_state(
                            state
                        )

                    else:
                        print(
                            f"Automation "
                            f"'{self.config.id}': "
                            f"target {target.get('id')} "
                            f"execution failed.",
                            flush=True,
                        )

                except Exception as exc:
                    print(
                        f"Automation "
                        f"'{self.config.id}': "
                        f"target {target.get('id')} "
                        f"failed: {exc}",
                        flush=True,
                    )

            self._wait()

    def _wait(self) -> None:
        import time

        time.sleep(
            self.config.check_interval_seconds
        )

    def _save_and_publish_state(
        self,
        state: dict[str, Any],
    ) -> None:
        state = {
            "automationId": self.config.id,
            "automationName": self.config.name,
            **state,
        }

        state_file = (
            Path(__file__).resolve().parent.parent.parent
            / self.config.state_file
        )

        save_state(
            state_file,
            state,
        )

        self._publish_state(
            state
        )

    def _publish_state(
        self,
        state: dict[str, Any],
    ) -> None:
        try:
            response = requests.post(
                self.INTERNAL_STATE_URL,
                json=state,
                timeout=5,
            )

            response.raise_for_status()

        except Exception as exc:
            print(
                f"Failed to publish automation state: "
                f"{exc}",
                flush=True,
            )