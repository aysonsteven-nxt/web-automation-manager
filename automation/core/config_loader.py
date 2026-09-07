import json
from pathlib import Path, PureWindowsPath
from urllib.parse import urlparse

from automation.core.config import AutomationConfig


class AutomationConfigLoader:
    CONFIG_FILE = (
        Path(__file__).resolve().parent.parent.parent
        / "automations.json"
    )

    @staticmethod
    def _validate_config_item(item: dict) -> None:
        web_config = item.get("config", {}).get("web", {})
        url = web_config.get("url", "")
        parsed_url = urlparse(url)

        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError(
                "Automation web URL must use http or https."
            )

        path_values = {
            "session_file": web_config.get("session_file"),
            "state_file": item.get("state_file"),
            "log_file": item.get("log_file"),
        }

        for field_name, path_value in path_values.items():
            if not isinstance(path_value, str) or not path_value.strip():
                raise ValueError(
                    f"Automation {field_name} must be a non-empty path."
                )

            path = Path(path_value)
            windows_path = PureWindowsPath(path_value)
            if (
                path.is_absolute()
                or windows_path.is_absolute()
                or ".." in path.parts
                or ".." in windows_path.parts
            ):
                raise ValueError(
                    f"Automation {field_name} must stay within the project."
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

        configs = []
        for item in automations:
            if not isinstance(item, dict):
                raise ValueError(
                    "Each automation configuration must be an object."
                )

            cls._validate_config_item(item)
            configs.append(AutomationConfig(**item))

        return configs

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