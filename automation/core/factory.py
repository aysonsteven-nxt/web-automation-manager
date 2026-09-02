from automation.core.strategy import AutomationStrategy
from automation.types.web.strategies.voting_strategy import (
    VotingStrategy,
)


class AutomationFactory:

    _strategies: dict[
        tuple[str, str],
        type[AutomationStrategy],
    ] = {
        (
            "web",
            "voting",
        ): VotingStrategy,
    }

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