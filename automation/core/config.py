from dataclasses import dataclass


@dataclass(frozen=True)
class AutomationConfig:
    id: str
    name: str
    type: str
    strategy: str
    url: str
    session_file: str
    state_file: str
    log_file: str
    check_interval_seconds: int
    action_delay_seconds: int
    enabled: bool