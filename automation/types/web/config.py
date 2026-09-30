from dataclasses import dataclass


@dataclass(frozen=True)
class WebAutomationConfig:
    url: str
    session_file: str