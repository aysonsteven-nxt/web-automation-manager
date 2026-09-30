from abc import ABC, abstractmethod

from automation.core.config import AutomationConfig


class Automation(ABC):
    """
    Base contract for all automation types.
    """

    def __init__(
        self,
        config: AutomationConfig,
    ):
        self.config = config

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError