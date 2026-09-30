from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AutomationConfig:
    id: str
    name: str
    type: str
    strategy: str
    config: dict[str, Any]
    state_file: str
    log_file: str
    check_interval_seconds: int
    enabled: bool