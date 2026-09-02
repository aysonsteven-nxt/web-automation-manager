from automation.forsaken_ro import ForsakenRoStrategy
from automation.strategy import AutomationStrategy


class AutomationFactory:

    _strategies: dict[str, type[AutomationStrategy]] = {
        "forsaken_ro": ForsakenRoStrategy,
    }

    @classmethod
    def create(
        cls,
        strategy_name: str,
    ) -> AutomationStrategy:

        strategy_class = cls._strategies.get(strategy_name)

        if strategy_class is None:
            raise ValueError(
                f"Unknown automation strategy: '{strategy_name}'"
            )

        return strategy_class()