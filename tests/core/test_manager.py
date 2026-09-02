from unittest.mock import MagicMock, patch

import pytest

from automation.core.config import AutomationConfig
from automation.core.manager import AutomationManager


def create_config(
    automation_id="test-automation",
    enabled=True,
):
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
        enabled=enabled,
    )


@pytest.fixture
def config():
    return create_config()


# ============================================================
# Initialization
# ============================================================


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_manager_loads_configured_automations(
    mock_process,
    mock_load_all,
):
    config_one = create_config(
        "automation-one"
    )

    config_two = create_config(
        "automation-two"
    )

    mock_load_all.return_value = [
        config_one,
        config_two,
    ]

    manager = AutomationManager()

    mock_load_all.assert_called_once_with()

    assert "automation-one" in manager.processes
    assert "automation-two" in manager.processes

    assert (
        manager.processes["automation-one"]
        is not None
    )

    assert (
        manager.processes["automation-two"]
        is not None
    )

    assert mock_process.call_count == 2


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_manager_creates_process_for_each_config(
    mock_process,
    mock_load_all,
):
    config_one = create_config(
        "automation-one"
    )

    config_two = create_config(
        "automation-two"
    )

    mock_load_all.return_value = [
        config_one,
        config_two,
    ]

    AutomationManager()

    assert mock_process.call_count == 2

    mock_process.assert_any_call(
        config_one
    )

    mock_process.assert_any_call(
        config_two
    )


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_manager_starts_with_empty_processes_when_no_configs(
    mock_process,
    mock_load_all,
):
    mock_load_all.return_value = []

    manager = AutomationManager()

    assert manager.processes == {}

    mock_process.assert_not_called()


# ============================================================
# get()
# ============================================================


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_get_returns_process(
    mock_process,
    mock_load_all,
):
    config = create_config()

    mock_load_all.return_value = [
        config
    ]

    process = MagicMock()

    mock_process.return_value = process

    manager = AutomationManager()

    result = manager.get(
        "test-automation"
    )

    assert result is process


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_get_raises_for_unknown_automation(
    mock_process,
    mock_load_all,
):
    mock_load_all.return_value = []

    manager = AutomationManager()

    with pytest.raises(
        KeyError,
        match="Automation 'missing' not found",
    ):
        manager.get(
            "missing"
        )


# ============================================================
# list()
# ============================================================


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_list_returns_all_processes(
    mock_process,
    mock_load_all,
):
    config_one = create_config(
        "automation-one"
    )

    config_two = create_config(
        "automation-two"
    )

    process_one = MagicMock()
    process_two = MagicMock()

    mock_load_all.return_value = [
        config_one,
        config_two,
    ]

    mock_process.side_effect = [
        process_one,
        process_two,
    ]

    manager = AutomationManager()

    result = manager.list()

    assert result == [
        process_one,
        process_two,
    ]


# ============================================================
# start()
# ============================================================


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_start_starts_enabled_automation(
    mock_process,
    mock_load_all,
):
    config = create_config(
        enabled=True
    )

    process = MagicMock()

    process.config = config

    mock_load_all.return_value = [
        config
    ]

    mock_process.return_value = process

    process.start.return_value = True

    manager = AutomationManager()

    result = manager.start(
        "test-automation"
    )

    assert result is True

    process.start.assert_called_once_with()


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_start_returns_false_when_process_already_running(
    mock_process,
    mock_load_all,
):
    config = create_config(
        enabled=True
    )

    process = MagicMock()

    process.config = config

    mock_load_all.return_value = [
        config
    ]

    mock_process.return_value = process

    process.start.return_value = False

    manager = AutomationManager()

    result = manager.start(
        "test-automation"
    )

    assert result is False

    process.start.assert_called_once_with()


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_start_raises_when_automation_is_disabled(
    mock_process,
    mock_load_all,
):
    config = create_config(
        enabled=False
    )

    process = MagicMock()

    # AutomationManager checks process.config.enabled
    process.config = config

    mock_load_all.return_value = [
        config
    ]

    mock_process.return_value = process

    manager = AutomationManager()

    with pytest.raises(
        ValueError,
        match="Automation 'test-automation' is disabled",
    ):
        manager.start(
            "test-automation"
        )

    process.start.assert_not_called()


# ============================================================
# stop()
# ============================================================


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_stop_stops_automation(
    mock_process,
    mock_load_all,
):
    config = create_config()

    process = MagicMock()

    process.config = config

    mock_load_all.return_value = [
        config
    ]

    mock_process.return_value = process

    process.stop.return_value = True

    manager = AutomationManager()

    result = manager.stop(
        "test-automation"
    )

    assert result is True

    process.stop.assert_called_once_with()


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_stop_returns_false_when_not_running(
    mock_process,
    mock_load_all,
):
    config = create_config()

    process = MagicMock()

    process.config = config

    mock_load_all.return_value = [
        config
    ]

    mock_process.return_value = process

    process.stop.return_value = False

    manager = AutomationManager()

    result = manager.stop(
        "test-automation"
    )

    assert result is False

    process.stop.assert_called_once_with()


# ============================================================
# stop_all()
# ============================================================


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_stop_all_stops_automation(
    mock_process,
    mock_load_all,
):
    config = create_config()

    process = MagicMock()

    process.config = config

    mock_load_all.return_value = [
        config
    ]

    mock_process.return_value = process

    process.stop_all.return_value = [
        1234
    ]

    manager = AutomationManager()

    result = manager.stop_all(
        "test-automation"
    )

    assert result == [
        1234
    ]

    process.stop_all.assert_called_once_with()


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_stop_all_returns_empty_list_when_nothing_running(
    mock_process,
    mock_load_all,
):
    config = create_config()

    process = MagicMock()

    process.config = config

    mock_load_all.return_value = [
        config
    ]

    mock_process.return_value = process

    process.stop_all.return_value = []

    manager = AutomationManager()

    result = manager.stop_all(
        "test-automation"
    )

    assert result == []

    process.stop_all.assert_called_once_with()


# ============================================================
# status()
# ============================================================


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_status_returns_process_status(
    mock_process,
    mock_load_all,
):
    config = create_config()

    process = MagicMock()

    process.config = config

    mock_load_all.return_value = [
        config
    ]

    mock_process.return_value = process

    expected_status = {
        "running": True,
        "pid": 1234,
        "returncode": None,
    }

    process.status.return_value = expected_status

    manager = AutomationManager()

    result = manager.status(
        "test-automation"
    )

    assert result == expected_status

    process.status.assert_called_once_with()


# ============================================================
# pids()
# ============================================================


@patch(
    "automation.core.manager.AutomationConfigLoader.load_all"
)
@patch(
    "automation.core.manager.AutomationProcess"
)
def test_pids_returns_worker_pids(
    mock_process,
    mock_load_all,
):
    config = create_config()

    process = MagicMock()

    process.config = config

    mock_load_all.return_value = [
        config
    ]

    mock_process.return_value = process

    process.get_worker_pids.return_value = [
        1234,
        5678,
    ]

    manager = AutomationManager()

    result = manager.pids(
        "test-automation"
    )

    assert result == [
        1234,
        5678,
    ]

    process.get_worker_pids.assert_called_once_with()