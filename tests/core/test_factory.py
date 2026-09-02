import pytest

from automation.core.config import AutomationConfig
from automation.core.factory import AutomationFactory
from automation.core.strategy import AutomationStrategy
from automation.types.web.automation import WebAutomation
from automation.types.web.strategies.voting_strategy import (
    VotingStrategy,
)


def create_config(
    automation_type: str = "web",
    strategy: str = "voting",
) -> AutomationConfig:
    return AutomationConfig(
        id="test",
        name="Test Automation",
        type=automation_type,
        strategy=strategy,
        url="https://example.com",
        session_file="test_session.json",
        state_file="state/test.json",
        log_file="logs/test.log",
        check_interval_seconds=60,
        action_delay_seconds=3,
        enabled=True,
    )


def test_create_web_automation():
    config = create_config()

    automation = AutomationFactory.create_automation(
        config
    )

    assert isinstance(
        automation,
        WebAutomation,
    )

    assert automation.config is config


def test_create_voting_strategy():
    strategy = AutomationFactory.create_strategy(
        "web",
        "voting",
    )

    assert isinstance(
        strategy,
        VotingStrategy,
    )

    assert isinstance(
        strategy,
        AutomationStrategy,
    )


def test_create_automation_with_unknown_type():
    config = create_config(
        automation_type="unknown",
    )

    with pytest.raises(
        ValueError,
        match="Unknown automation type",
    ):
        AutomationFactory.create_automation(
            config
        )


def test_create_strategy_with_unknown_type():
    with pytest.raises(
        ValueError,
        match="Unknown automation strategy",
    ):
        AutomationFactory.create_strategy(
            "unknown",
            "voting",
        )


def test_create_strategy_with_unknown_strategy():
    with pytest.raises(
        ValueError,
        match="Unknown automation strategy",
    ):
        AutomationFactory.create_strategy(
            "web",
            "unknown",
        )