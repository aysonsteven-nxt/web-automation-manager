import pytest

from automation.core.config import AutomationConfig
from automation.core.factory import AutomationFactory
from automation.types.web.automation import WebAutomation
from automation.types.web.strategies.voting_strategy import VotingStrategy


def create_config(
    automation_type="web",
    strategy="voting",
) -> AutomationConfig:
    return AutomationConfig(
        id="test",
        name="Test Automation",
        type=automation_type,
        strategy=strategy,
        config={
            "web": {
                "url": "https://example.com",
                "session_file": "test_session.json",
            },
            "strategy": {
                "action_delay_seconds": 3,
            },
        },
        state_file="state/test.json",
        log_file="logs/test.log",
        check_interval_seconds=60,
        enabled=True,
    )


def test_create_web_automation():
    config = create_config()

    automation = AutomationFactory.create_automation(
        config,
    )

    assert isinstance(
        automation,
        WebAutomation,
    )
    assert automation.config == config


def test_create_voting_strategy():
    config = create_config(
        automation_type="web",
        strategy="voting",
    )

    strategy = AutomationFactory.create_strategy(
        config,
    )

    assert isinstance(
        strategy,
        VotingStrategy,
    )
    assert (
        strategy.strategy_config.action_delay_seconds
        == 3
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
            config,
        )


def test_create_strategy_with_unknown_type():
    config = create_config(
        automation_type="unknown",
        strategy="voting",
    )

    with pytest.raises(
        ValueError,
        match="Unknown automation strategy",
    ):
        AutomationFactory.create_strategy(
            config,
        )


def test_create_strategy_with_unknown_strategy():
    config = create_config(
        automation_type="web",
        strategy="unknown",
    )

    with pytest.raises(
        ValueError,
        match="Unknown automation strategy",
    ):
        AutomationFactory.create_strategy(
            config,
        )