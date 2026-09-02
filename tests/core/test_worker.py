from unittest.mock import MagicMock, patch

import pytest

from automation.core.config import AutomationConfig
from automation.core.worker import AutomationWorker


def create_config() -> AutomationConfig:
    return AutomationConfig(
        id="test",
        name="Test Automation",
        type="web",
        strategy="voting",
        url="https://example.com",
        session_file="test_session.json",
        state_file="state/test.json",
        log_file="logs/test.log",
        check_interval_seconds=60,
        action_delay_seconds=3,
        enabled=True,
    )


def create_worker() -> AutomationWorker:
    return AutomationWorker(
        create_config()
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
        worker.config
    )

    create_strategy.assert_called_once_with(
        "web",
        "voting",
    )

    assert worker.automation is automation
    assert worker.strategy is strategy


def test_worker_starts_and_closes_automation():
    automation = MagicMock()
    strategy = MagicMock()

    strategy.check.side_effect = [
        {
            "status": "running",
            "targets": [],
        }
    ]

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ), patch.object(
        AutomationWorker,
        "_save_and_publish_state",
    ), patch.object(
        AutomationWorker,
        "_wait",
        side_effect=StopIteration,
    ):

        worker = create_worker()

        with pytest.raises(StopIteration):
            worker.run()

    automation.start.assert_called_once()
    automation.close.assert_called_once()


def test_worker_checks_strategy():
    automation = MagicMock()
    strategy = MagicMock()

    state = {
        "status": "running",
        "targets": [],
    }

    strategy.check.return_value = state

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ), patch.object(
        AutomationWorker,
        "_save_and_publish_state",
    ), patch.object(
        AutomationWorker,
        "_wait",
        side_effect=StopIteration,
    ):

        worker = create_worker()

        with pytest.raises(StopIteration):
            worker.run()

    strategy.check.assert_called_once_with(
        automation
    )


def test_worker_gets_targets_from_strategy():
    automation = MagicMock()
    strategy = MagicMock()

    state = {
        "status": "running",
    }

    targets = [
        {
            "id": "target-1",
        },
        {
            "id": "target-2",
        },
    ]

    strategy.check.return_value = state
    strategy.get_targets.return_value = targets

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ), patch.object(
        AutomationWorker,
        "_save_and_publish_state",
    ), patch.object(
        AutomationWorker,
        "_wait",
        side_effect=StopIteration,
    ):

        worker = create_worker()

        with pytest.raises(StopIteration):
            worker.run()

    strategy.get_targets.assert_called_once_with(
        state
    )


def test_worker_executes_targets():
    automation = MagicMock()
    strategy = MagicMock()

    state = {
        "status": "running",
    }

    targets = [
        {
            "id": "target-1",
        },
        {
            "id": "target-2",
        },
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
        "_save_and_publish_state",
    ), patch.object(
        AutomationWorker,
        "_wait",
        side_effect=StopIteration,
    ):

        worker = create_worker()

        with pytest.raises(StopIteration):
            worker.run()

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
        "status": "running",
    }

    updated_state = {
        "status": "updated",
    }

    targets = [
        {
            "id": "target-1",
        },
    ]

    strategy.check.side_effect = [
        initial_state,
        updated_state,
    ]

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
        "_save_and_publish_state",
    ) as save_state, patch.object(
        AutomationWorker,
        "_wait",
        side_effect=StopIteration,
    ):

        worker = create_worker()

        with pytest.raises(StopIteration):
            worker.run()

    assert strategy.check.call_count == 2

    strategy.check.assert_any_call(
        automation
    )

    assert save_state.call_count == 2

    save_state.assert_any_call(
        initial_state
    )

    save_state.assert_any_call(
        updated_state
    )


def test_worker_does_not_recheck_after_failed_execution():
    automation = MagicMock()
    strategy = MagicMock()

    state = {
        "status": "running",
    }

    targets = [
        {
            "id": "target-1",
        },
    ]

    strategy.check.return_value = state
    strategy.get_targets.return_value = targets
    strategy.execute.return_value = False

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ), patch.object(
        AutomationWorker,
        "_save_and_publish_state",
    ), patch.object(
        AutomationWorker,
        "_wait",
        side_effect=StopIteration,
    ):

        worker = create_worker()

        with pytest.raises(StopIteration):
            worker.run()

    strategy.check.assert_called_once_with(
        automation
    )

    strategy.execute.assert_called_once_with(
        automation,
        targets[0],
    )


def test_worker_continues_when_target_execution_fails():
    automation = MagicMock()
    strategy = MagicMock()

    state = {
        "status": "running",
    }

    targets = [
        {
            "id": "target-1",
        },
        {
            "id": "target-2",
        },
    ]

    strategy.check.return_value = state
    strategy.get_targets.return_value = targets

    strategy.execute.side_effect = [
        Exception("Target failed"),
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
        "_save_and_publish_state",
    ), patch.object(
        AutomationWorker,
        "_wait",
        side_effect=StopIteration,
    ):

        worker = create_worker()

        with pytest.raises(StopIteration):
            worker.run()

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

    automation.start.side_effect = (
        RuntimeError("Startup failed")
    )

    with patch(
        "automation.core.worker.AutomationFactory.create_automation",
        return_value=automation,
    ), patch(
        "automation.core.worker.AutomationFactory.create_strategy",
        return_value=strategy,
    ):

        worker = create_worker()

        with pytest.raises(
            RuntimeError,
            match="Startup failed",
        ):
            worker.run()

    automation.start.assert_called_once()
    automation.close.assert_called_once()


def test_worker_saves_and_publishes_state():
    worker = create_worker()

    state = {
        "credits": 100,
        "targets": [],
    }

    with patch(
        "automation.core.worker.save_state"
    ) as save_state, patch.object(
        worker,
        "_publish_state",
    ) as publish_state:

        worker._save_and_publish_state(
            state
        )

    expected_state = {
        "automationId": "test",
        "automationName": "Test Automation",
        "credits": 100,
        "targets": [],
    }

    save_state.assert_called_once()

    save_args = save_state.call_args.args

    assert save_args[0].name == "test.json"
    assert save_args[0].parent.name == "state"

    assert save_args[1] == expected_state

    publish_state.assert_called_once_with(
        expected_state
    )