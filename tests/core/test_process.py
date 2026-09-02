import subprocess
from unittest.mock import MagicMock, patch

from automation.core.config import AutomationConfig
from automation.core.process import AutomationProcess


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


def create_process() -> AutomationProcess:
    return AutomationProcess(
        create_config()
    )


def test_initial_status():
    process = create_process()

    assert process.is_running() is False

    assert process.status() == {
        "running": False,
        "pid": None,
        "returncode": None,
    }


def test_start_worker():
    process = create_process()

    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_process.pid = 12345

    with patch(
        "automation.core.process.subprocess.Popen",
        return_value=mock_process,
    ) as mock_popen:

        result = process.start()

    assert result is True
    assert process.process is mock_process

    mock_popen.assert_called_once()

    args, kwargs = mock_popen.call_args

    command = args[0]

    assert command[1] == str(
        process.WORKER_SCRIPT
    )

    assert command[2] == "test"

    assert kwargs["cwd"] == (
        process.WORKER_SCRIPT.parent
    )


def test_start_does_not_start_if_already_running():
    process = create_process()

    existing_process = MagicMock()
    existing_process.poll.return_value = None
    existing_process.pid = 12345

    process.process = existing_process

    with patch(
        "automation.core.process.subprocess.Popen"
    ) as mock_popen:

        result = process.start()

    assert result is False

    mock_popen.assert_not_called()

    assert process.process is existing_process


def test_stop_worker():
    process = create_process()

    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_process.pid = 12345

    process.process = mock_process

    result = process.stop()

    assert result is True

    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once_with(
        timeout=10
    )


def test_stop_does_nothing_when_not_running():
    process = create_process()

    result = process.stop()

    assert result is False


def test_stop_kills_worker_after_terminate_timeout():
    process = create_process()

    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_process.pid = 12345

    mock_process.wait.side_effect = (
        subprocess.TimeoutExpired(
            cmd="test",
            timeout=10,
        ),
        None,
    )

    process.process = mock_process

    result = process.stop()

    assert result is True

    mock_process.terminate.assert_called_once()
    mock_process.kill.assert_called_once()

    assert mock_process.wait.call_count == 2

    mock_process.wait.assert_any_call(
        timeout=10
    )

    mock_process.wait.assert_any_call(
        timeout=5
    )


def test_stop_all():
    process = create_process()

    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_process.pid = 12345

    process.process = mock_process

    result = process.stop_all()

    assert result == [12345]

    mock_process.terminate.assert_called_once()


def test_stop_all_when_not_running():
    process = create_process()

    result = process.stop_all()

    assert result == []


def test_status_when_running():
    process = create_process()

    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_process.pid = 12345

    process.process = mock_process

    assert process.status() == {
        "running": True,
        "pid": 12345,
        "returncode": None,
    }


def test_status_when_stopped():
    process = create_process()

    mock_process = MagicMock()
    mock_process.poll.return_value = 1
    mock_process.pid = 12345

    process.process = mock_process

    assert process.status() == {
        "running": False,
        "pid": 12345,
        "returncode": 1,
    }


def test_get_worker_pids_when_running():
    process = create_process()

    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_process.pid = 12345

    process.process = mock_process

    assert process.get_worker_pids() == [
        12345
    ]


def test_get_worker_pids_when_not_running():
    process = create_process()

    assert process.get_worker_pids() == []