import sys

from automation.core.config_loader import AutomationConfigLoader
from automation.core.worker import AutomationWorker


def main() -> None:
    if len(sys.argv) != 2:
        raise ValueError(
            "Usage: "
            "python run_automation.py <automation_id>"
        )

    automation_id = sys.argv[1]

    config = AutomationConfigLoader.load_by_id(
        automation_id
    )

    worker = AutomationWorker(
        config
    )

    worker.run()


if __name__ == "__main__":
    main()