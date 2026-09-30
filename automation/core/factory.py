from typing import Any, Callable

from automation.core.config import AutomationConfig
from automation.core.strategy import AutomationStrategy
from automation.types.web.automation import WebAutomation
from automation.types.web.strategies.config import VotingStrategyConfig
from automation.types.web.strategies.voting_strategy import VotingStrategy


class AutomationFactory:
    _automation_types = {
        "web": WebAutomation,
    }

    _strategies: dict[
        tuple[str, str],
        Callable[[Any], AutomationStrategy],
    ] = {
        ("web", "voting"): VotingStrategy,
    }

    @classmethod
    def create_automation(
        cls,
        config: AutomationConfig,
    ):
        automation_class = cls._automation_types.get(config.type)

        if automation_class is None:
            raise ValueError(
                f"Unknown automation type: '{config.type}'"
            )

        return automation_class(config)

    @classmethod
    def create_strategy(
        cls,
        config: AutomationConfig,
    ) -> AutomationStrategy:
        key = (
            config.type,
            config.strategy,
        )

        strategy_class = cls._strategies.get(key)

        if strategy_class is None:
            raise ValueError(
                f"Unknown automation strategy: "
                f"type='{config.type}', "
                f"strategy='{config.strategy}'"
            )

        if key == ("web", "voting"):
            strategy_config = VotingStrategyConfig(
                action_delay_seconds=config.config[
                    "strategy"
                ]["action_delay_seconds"]
            )

            return strategy_class(strategy_config)

        raise ValueError(
            f"Strategy configuration is not implemented: "
            f"type='{config.type}', "
            f"strategy='{config.strategy}'"
        )