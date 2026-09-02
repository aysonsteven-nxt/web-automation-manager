from automation.core.config import AutomationConfig
from automation.core.strategy import AutomationStrategy
from automation.types.web.automation import WebAutomation
from automation.types.web.strategies.voting_strategy import (
    VotingStrategy,
)


class AutomationFactory:
    """
    Factory for creating automation types and strategies.
    """

    _automation_types = {
        "web": WebAutomation,
    }

    _strategies: dict[
        tuple[str, str],
        type[AutomationStrategy],
    ] = {
        ("web", "voting"): VotingStrategy,
    }

    @classmethod
    def create_automation(
        cls,
        config: AutomationConfig,
    ):
        automation_class = cls._automation_types.get(
            config.type
        )

        if automation_class is None:
            raise ValueError(
                f"Unknown automation type: "
                f"'{config.type}'"
            )

        return automation_class(config)

    @classmethod
    def create_strategy(
        cls,
        automation_type: str,
        strategy_name: str,
    ) -> AutomationStrategy:

        key = (
            automation_type,
            strategy_name,
        )

        strategy_class = cls._strategies.get(key)

        if strategy_class is None:
            raise ValueError(
                f"Unknown automation strategy: "
                f"type='{automation_type}', "
                f"strategy='{strategy_name}'"
            )

        return strategy_class()