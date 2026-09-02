import argparse

from automation.config_loader import AutomationConfigLoader
from automation.factory import AutomationFactory
from automation.worker import AutomationWorker


def main():
    parser = argparse.ArgumentParser(
        description="Web Automation Manager worker"
    )

    parser.add_argument(
        "--automation-id",
        required=True,
        help="ID of the automation to run",
    )

    args = parser.parse_args()

    config = AutomationConfigLoader.load_by_id(
        args.automation_id
    )

    strategy = AutomationFactory.create(
        config.strategy
    )

    worker = AutomationWorker(
        config=config,
        strategy=strategy,
    )

    worker.run()


if __name__ == "__main__":
    main()