import json
from pathlib import Path

from automation.core.config import AutomationConfig


class AutomationConfigLoader:
    CONFIG_FILE = (
        Path(__file__).resolve().parent.parent.parent
        / "automations.json"
    )

    @classmethod
    def load_all(cls) -> list[AutomationConfig]:
        if not cls.CONFIG_FILE.exists():
            raise FileNotFoundError(
                f"Automation configuration not found: {cls.CONFIG_FILE}"
            )

        with cls.CONFIG_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        automations = data.get("automations")

        if automations is None:
            raise ValueError(
                "Missing 'automations' property in automations.json"
            )

        if not isinstance(automations, list):
            raise ValueError(
                "'automations' must be an array in automations.json"
            )

        return [
            AutomationConfig(**item)
            for item in automations
        ]

    @classmethod
    def load_by_id(
        cls,
        automation_id: str,
    ) -> AutomationConfig:
        for config in cls.load_all():
            if config.id == automation_id:
                return config

        raise ValueError(
            f"Automation '{automation_id}' not found"
        )