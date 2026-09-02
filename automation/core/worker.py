import time
from pathlib import Path
from typing import Any

import requests

from automation.core.config import AutomationConfig
from automation.core.factory import AutomationFactory
from automation.core.state import save_state


class AutomationWorker:
    """
    Executes a configured automation.

    The worker is responsible for orchestration only.

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

        self.automation = (
            AutomationFactory.create_automation(
                config
            )
        )

        self.strategy = (
            AutomationFactory.create_strategy(
                config.type,
                config.strategy,
            )
        )

    def run(self) -> None:
        print(
            f"Starting automation: "
            f"{self.config.name}",
            flush=True,
        )

        try:
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
            self.automation.close()

            print(
                f"Automation stopped: "
                f"{self.config.name}",
                flush=True,
            )

    def _execute(self) -> None:

        while True:

            state = self.strategy.check(
                self.automation
            )

            self._save_and_publish_state(
                state
            )

            targets = self.strategy.get_targets(
                state
            )

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
                            f"target "
                            f"{target.get('id')} "
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
                            f"target "
                            f"{target.get('id')} "
                            f"execution failed.",
                            flush=True,
                        )

                except Exception as exc:
                    print(
                        f"Automation "
                        f"'{self.config.id}': "
                        f"target "
                        f"{target.get('id')} "
                        f"failed: {exc}",
                        flush=True,
                    )

            self._wait()

    def _wait(self) -> None:
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