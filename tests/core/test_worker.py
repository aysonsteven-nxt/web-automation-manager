from pathlib import Path
from unittest.mock import MagicMock, patch

from automation.core.config import AutomationConfig
from automation.core.worker import AutomationWorker


def create_config(
    automation_id="test",
) -> AutomationConfig:
    return AutomationConfig(
        id=automation_id,
        name="Test Automation",
        type="web",
        strategy="voting",
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


def create_worker():
    return AutomationWorker(
        create_config(),
    )


def test_worker_creates_automation_and_strategy():
    automation = MagicMock()
    strategy = MagicMock()

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ) as create_automation, patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ) as create_strategy:

        worker = create_worker()

    create_automation.assert_called_once_with(
        worker.config,
    )

    create_strategy.assert_called_once_with(
        worker.config,
    )

    assert worker.automation is automation
    assert worker.strategy is strategy


def test_worker_starts_and_closes_automation():
    automation = MagicMock()
    strategy = MagicMock()

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ), patch.object(
        AutomationWorker,
        "_execute",
    ) as execute:

        worker = create_worker()
        worker.run()

    automation.start.assert_called_once()
    strategy.initialize.assert_called_once_with(
        automation,
    )
    execute.assert_called_once()
    automation.close.assert_called_once()


def test_worker_checks_strategy():
    automation = MagicMock()
    strategy = MagicMock()

    state = {
        "credits": 100,
        "providers": [],
    }

    strategy.check.return_value = state
    strategy.get_targets.return_value = []

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ), patch.object(
        AutomationWorker,
        "_wait",
        side_effect=KeyboardInterrupt,
    ), patch.object(
        AutomationWorker,
        "_save_and_publish_state",
    ):

        worker = create_worker()

        try:
            worker._execute()
        except KeyboardInterrupt:
            pass

    strategy.check.assert_called_once_with(
        automation,
    )


def test_worker_gets_targets_from_strategy():
    automation = MagicMock()
    strategy = MagicMock()

    state = {
        "credits": 100,
        "providers": [],
    }

    strategy.check.return_value = state
    strategy.get_targets.return_value = []

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ), patch.object(
        AutomationWorker,
        "_wait",
        side_effect=KeyboardInterrupt,
    ), patch.object(
        AutomationWorker,
        "_save_and_publish_state",
    ):

        worker = create_worker()

        try:
            worker._execute()
        except KeyboardInterrupt:
            pass

    strategy.get_targets.assert_called_once_with(
        state,
    )


def test_worker_executes_targets():
    automation = MagicMock()
    strategy = MagicMock()

    state = {
        "credits": 100,
        "providers": [],
    }

    targets = [
        {"id": "1"},
        {"id": "2"},
    ]

    strategy.check.return_value = state
    strategy.get_targets.return_value = targets
    strategy.execute.return_value = True

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ), patch.object(
        AutomationWorker,
        "_wait",
        side_effect=KeyboardInterrupt,
    ), patch.object(
        AutomationWorker,
        "_save_and_publish_state",
    ):

        worker = create_worker()

        try:
            worker._execute()
        except KeyboardInterrupt:
            pass

    assert strategy.execute.call_count == 2

    strategy.execute.assert_any_call(
        automation,
        targets[0],
    )

    strategy.execute.assert_any_call(
        automation,
        targets[1],
    )


def test_worker_rechecks_state_after_successful_execution():
    automation = MagicMock()
    strategy = MagicMock()

    initial_state = {
        "credits": 100,
        "providers": [],
    }

    updated_state = {
        "credits": 101,
        "providers": [],
    }

    strategy.check.side_effect = [
        initial_state,
        updated_state,
    ]

    strategy.get_targets.return_value = [
        {"id": "1"},
    ]

    strategy.execute.return_value = True

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ), patch.object(
        AutomationWorker,
        "_wait",
        side_effect=KeyboardInterrupt,
    ), patch.object(
        AutomationWorker,
        "_save_and_publish_state",
    ):

        worker = create_worker()

        try:
            worker._execute()
        except KeyboardInterrupt:
            pass

    assert strategy.check.call_count == 2

    strategy.check.assert_any_call(
        automation,
    )


def test_worker_does_not_recheck_after_failed_execution():
    automation = MagicMock()
    strategy = MagicMock()

    state = {
        "credits": 100,
        "providers": [],
    }

    strategy.check.return_value = state

    strategy.get_targets.return_value = [
        {"id": "1"},
    ]

    strategy.execute.return_value = False

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ), patch.object(
        AutomationWorker,
        "_wait",
        side_effect=KeyboardInterrupt,
    ), patch.object(
        AutomationWorker,
        "_save_and_publish_state",
    ):

        worker = create_worker()

        try:
            worker._execute()
        except KeyboardInterrupt:
            pass

    strategy.check.assert_called_once_with(
        automation,
    )


def test_worker_continues_when_target_execution_fails():
    automation = MagicMock()
    strategy = MagicMock()

    state = {
        "credits": 100,
        "providers": [],
    }

    targets = [
        {"id": "1"},
        {"id": "2"},
    ]

    strategy.check.return_value = state
    strategy.get_targets.return_value = targets

    strategy.execute.side_effect = [
        Exception("first target failed"),
        True,
    ]

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ), patch.object(
        AutomationWorker,
        "_wait",
        side_effect=KeyboardInterrupt,
    ), patch.object(
        AutomationWorker,
        "_save_and_publish_state",
    ):

        worker = create_worker()

        try:
            worker._execute()
        except KeyboardInterrupt:
            pass

    assert strategy.execute.call_count == 2

    strategy.execute.assert_any_call(
        automation,
        targets[0],
    )

    strategy.execute.assert_any_call(
        automation,
        targets[1],
    )


def test_worker_closes_automation_when_start_fails():
    automation = MagicMock()
    strategy = MagicMock()

    automation.start.side_effect = Exception(
        "start failed"
    )

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ):

        worker = create_worker()

        try:
            worker.run()
        except Exception as exc:
            assert str(exc) == "start failed"

    automation.start.assert_called_once()
    automation.close.assert_called_once()

    strategy.initialize.assert_not_called()


def test_worker_saves_and_publishes_state():
    automation = MagicMock()
    strategy = MagicMock()

    state = {
        "credits": 100,
        "providers": [],
    }

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ), patch(
        "automation.core.worker.save_state",
    ) as save_state, patch.object(
        AutomationWorker,
        "_publish_state",
    ) as publish_state:

        worker = create_worker()

        worker._save_and_publish_state(
            state,
        )

    expected_state = {
        "automationId": "test",
        "automationName": "Test Automation",
        "credits": 100,
        "providers": [],
    }

    expected_state_file = (
        Path(__file__).resolve().parent.parent.parent
        / worker.config.state_file
    )

    save_state.assert_called_once_with(
        expected_state_file,
        expected_state,
    )

    publish_state.assert_called_once_with(
        expected_state,
    )