from abc import ABC, abstractmethod
from typing import Any


class AutomationStrategy(ABC):

    @abstractmethod
    def check(self, page) -> dict[str, Any]:
        """
        Inspect the target website and return its current state.
        """
        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        context,
        page,
        target: dict[str, Any],
    ) -> bool:
        """
        Execute an automation action against the target.
        """
        raise NotImplementedError