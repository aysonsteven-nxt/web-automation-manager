from dataclasses import dataclass


@dataclass(frozen=True)
class VotingStrategyConfig:
    action_delay_seconds: int