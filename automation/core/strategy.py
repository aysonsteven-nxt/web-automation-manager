from abc import ABC, abstractmethod
from typing import Any


class AutomationStrategy(ABC):

    @abstractmethod
    def initialize(self, automation) -> None:
        raise NotImplementedError

    @abstractmethod
    def check(self, automation) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_targets(
        self,
        state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        automation,
        target: dict[str, Any],
    ) -> bool:
        raise NotImplementedError