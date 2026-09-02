from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


# ============================================================
# GET /api/hello
# ============================================================


def test_hello():
    response = client.get(
        "/api/hello"
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Automation API is working!"
    }


# ============================================================
# GET /api/automations
# ============================================================


@patch("api.automation_manager")
def test_automation_list(
    mock_manager,
):
    process = MagicMock()

    process.config.id = "test-automation"
    process.config.name = "Test Automation"
    process.config.type = "web"
    process.config.strategy = "voting"
    process.config.url = "https://example.com"
    process.config.enabled = True

    process.status.return_value = {
        "running": True,
        "pid": 1234,
        "returncode": None,
    }

    mock_manager.list.return_value = [
        process
    ]

    response = client.get(
        "/api/automations"
    )

    assert response.status_code == 200

    assert response.json() == [
        {
            "id": "test-automation",
            "name": "Test Automation",
            "type": "web",
            "strategy": "voting",
            "url": "https://example.com",
            "enabled": True,
            "status": {
                "running": True,
                "pid": 1234,
                "returncode": None,
            },
        }
    ]

    mock_manager.list.assert_called_once_with()
    process.status.assert_called_once_with()


@patch("api.automation_manager")
def test_automation_list_returns_empty_list(
    mock_manager,
):
    mock_manager.list.return_value = []

    response = client.get(
        "/api/automations"
    )

    assert response.status_code == 200
    assert response.json() == []


# ============================================================
# GET /api/automations/{id}/status
# ============================================================


@patch("api.automation_manager")
def test_automation_status(
    mock_manager,
):
    expected_status = {
        "running": True,
        "pid": 1234,
        "returncode": None,
    }

    mock_manager.status.return_value = (
        expected_status
    )

    response = client.get(
        "/api/automations/test-automation/status"
    )

    assert response.status_code == 200
    assert response.json() == expected_status

    mock_manager.status.assert_called_once_with(
        "test-automation"
    )


@patch("api.automation_manager")
def test_automation_status_returns_404_for_unknown_automation(
    mock_manager,
):
    mock_manager.status.side_effect = KeyError(
        "Automation 'missing' not found"
    )

    response = client.get(
        "/api/automations/missing/status"
    )

    assert response.status_code == 404
    assert "Automation 'missing' not found" in response.json()["detail"]


@patch("api.automation_manager")
def test_automation_status_returns_404_for_value_error(
    mock_manager,
):
    mock_manager.status.side_effect = ValueError(
        "Invalid automation"
    )

    response = client.get(
        "/api/automations/test/status"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Invalid automation"
    }


# ============================================================
# GET /api/automations/{id}/pids
# ============================================================


@patch("api.automation_manager")
def test_automation_pids(
    mock_manager,
):
    mock_manager.pids.return_value = [
        1234,
        5678,
    ]

    response = client.get(
        "/api/automations/test-automation/pids"
    )

    assert response.status_code == 200

    assert response.json() == {
        "automationId": "test-automation",
        "count": 2,
        "pids": [
            1234,
            5678,
        ],
    }

    mock_manager.pids.assert_called_once_with(
        "test-automation"
    )


@patch("api.automation_manager")
def test_automation_pids_returns_empty_when_no_workers(
    mock_manager,
):
    mock_manager.pids.return_value = []

    response = client.get(
        "/api/automations/test-automation/pids"
    )

    assert response.status_code == 200

    assert response.json() == {
        "automationId": "test-automation",
        "count": 0,
        "pids": [],
    }


@patch("api.automation_manager")
def test_automation_pids_returns_404_for_unknown_automation(
    mock_manager,
):
    mock_manager.pids.side_effect = KeyError(
        "Automation 'missing' not found"
    )

    response = client.get(
        "/api/automations/missing/pids"
    )

    assert response.status_code == 404


# ============================================================
# POST /api/automations/{id}/start
# ============================================================


@patch("api.event_manager")
@patch("api.automation_manager")
def test_start_automation_success(
    mock_manager,
    mock_events,
):
    mock_manager.start.return_value = True

    expected_status = {
        "running": True,
        "pid": 1234,
        "returncode": None,
    }

    mock_manager.status.return_value = (
        expected_status
    )

    mock_events.broadcast = AsyncMock()

    response = client.post(
        "/api/automations/test-automation/start"
    )

    assert response.status_code == 200

    assert response.json() == {
        "started": True,
        **expected_status,
    }

    mock_manager.start.assert_called_once_with(
        "test-automation"
    )

    mock_manager.status.assert_called_once_with(
        "test-automation"
    )

    mock_events.broadcast.assert_awaited_once_with(
        "automation_status",
        expected_status,
    )


@patch("api.event_manager")
@patch("api.automation_manager")
def test_start_automation_when_already_running(
    mock_manager,
    mock_events,
):
    mock_manager.start.return_value = False

    expected_status = {
        "running": True,
        "pid": 1234,
        "returncode": None,
    }

    mock_manager.status.return_value = (
        expected_status
    )

    mock_events.broadcast = AsyncMock()

    response = client.post(
        "/api/automations/test-automation/start"
    )

    assert response.status_code == 200

    assert response.json() == {
        "started": False,
        **expected_status,
    }

    mock_events.broadcast.assert_not_awaited()


@patch("api.automation_manager")
def test_start_automation_returns_404_for_unknown_automation(
    mock_manager,
):
    mock_manager.start.side_effect = KeyError(
        "Automation 'missing' not found"
    )

    response = client.post(
        "/api/automations/missing/start"
    )

    assert response.status_code == 404


@patch("api.automation_manager")
def test_start_automation_returns_500_for_unexpected_error(
    mock_manager,
):
    mock_manager.start.side_effect = Exception(
        "Unexpected failure"
    )

    response = client.post(
        "/api/automations/test/start"
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": "Unexpected failure"
    }


# ============================================================
# POST /api/automations/{id}/stop
# ============================================================


@patch("api.event_manager")
@patch("api.automation_manager")
def test_stop_automation_success(
    mock_manager,
    mock_events,
):
    mock_manager.stop.return_value = True

    expected_status = {
        "running": False,
        "pid": 1234,
        "returncode": 0,
    }

    mock_manager.status.return_value = (
        expected_status
    )

    mock_events.broadcast = AsyncMock()

    response = client.post(
        "/api/automations/test-automation/stop"
    )

    assert response.status_code == 200

    assert response.json() == {
        "stopped": True,
        **expected_status,
    }

    mock_manager.stop.assert_called_once_with(
        "test-automation"
    )

    mock_events.broadcast.assert_awaited_once_with(
        "automation_status",
        expected_status,
    )


@patch("api.event_manager")
@patch("api.automation_manager")
def test_stop_automation_when_not_running(
    mock_manager,
    mock_events,
):
    mock_manager.stop.return_value = False

    expected_status = {
        "running": False,
        "pid": None,
        "returncode": None,
    }

    mock_manager.status.return_value = (
        expected_status
    )

    mock_events.broadcast = AsyncMock()

    response = client.post(
        "/api/automations/test-automation/stop"
    )

    assert response.status_code == 200

    assert response.json() == {
        "stopped": False,
        **expected_status,
    }

    mock_events.broadcast.assert_not_awaited()


@patch("api.automation_manager")
def test_stop_automation_returns_404_for_unknown_automation(
    mock_manager,
):
    mock_manager.stop.side_effect = KeyError(
        "Automation 'missing' not found"
    )

    response = client.post(
        "/api/automations/missing/stop"
    )

    assert response.status_code == 404


@patch("api.automation_manager")
def test_stop_automation_returns_500_for_unexpected_error(
    mock_manager,
):
    mock_manager.stop.side_effect = Exception(
        "Unexpected failure"
    )

    response = client.post(
        "/api/automations/test/stop"
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": "Unexpected failure"
    }


# ============================================================
# POST /api/automations/{id}/stop-all
# ============================================================


@patch("api.event_manager")
@patch("api.automation_manager")
def test_stop_all_automation_workers(
    mock_manager,
    mock_events,
):
    stopped_pids = [
        1234,
        5678,
    ]

    expected_status = {
        "running": False,
        "pid": None,
        "returncode": 0,
    }

    mock_manager.stop_all.return_value = (
        stopped_pids
    )

    mock_manager.status.return_value = (
        expected_status
    )

    mock_events.broadcast = AsyncMock()

    response = client.post(
        "/api/automations/test-automation/stop-all"
    )

    assert response.status_code == 200

    assert response.json() == {
        "automationId": "test-automation",
        "stopped": 2,
        "pids": [
            1234,
            5678,
        ],
        **expected_status,
    }

    mock_manager.stop_all.assert_called_once_with(
        "test-automation"
    )

    mock_manager.status.assert_called_once_with(
        "test-automation"
    )

    mock_events.broadcast.assert_awaited_once_with(
        "automation_status",
        expected_status,
    )


@patch("api.event_manager")
@patch("api.automation_manager")
def test_stop_all_when_no_workers_are_running(
    mock_manager,
    mock_events,
):
    expected_status = {
        "running": False,
        "pid": None,
        "returncode": None,
    }

    mock_manager.stop_all.return_value = []
    mock_manager.status.return_value = (
        expected_status
    )

    mock_events.broadcast = AsyncMock()

    response = client.post(
        "/api/automations/test-automation/stop-all"
    )

    assert response.status_code == 200

    assert response.json() == {
        "automationId": "test-automation",
        "stopped": 0,
        "pids": [],
        **expected_status,
    }

    mock_events.broadcast.assert_awaited_once_with(
        "automation_status",
        expected_status,
    )


@patch("api.automation_manager")
def test_stop_all_returns_404_for_unknown_automation(
    mock_manager,
):
    mock_manager.stop_all.side_effect = KeyError(
        "Automation 'missing' not found"
    )

    response = client.post(
        "/api/automations/missing/stop-all"
    )

    assert response.status_code == 404


@patch("api.automation_manager")
def test_stop_all_returns_500_for_unexpected_error(
    mock_manager,
):
    mock_manager.stop_all.side_effect = Exception(
        "Unexpected failure"
    )

    response = client.post(
        "/api/automations/test/stop-all"
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": "Unexpected failure"
    }


# ============================================================
# GET /api/automations/{id}/state
# ============================================================


@patch("api.load_state")
@patch("api.automation_manager")
def test_automation_state_returns_state(
    mock_manager,
    mock_load_state,
):
    process = MagicMock()

    process.config.state_file = (
        "state/test.json"
    )

    mock_manager.get.return_value = process

    expected_state = {
        "automationId": "test-automation",
        "credits": 100,
    }

    mock_load_state.return_value = (
        expected_state
    )

    response = client.get(
        "/api/automations/test-automation/state"
    )

    assert response.status_code == 200

    assert response.json() == expected_state

    mock_manager.get.assert_called_once_with(
        "test-automation"
    )

    mock_load_state.assert_called_once()


@patch("api.load_state")
@patch("api.automation_manager")
def test_automation_state_returns_404_when_state_does_not_exist(
    mock_manager,
    mock_load_state,
):
    process = MagicMock()

    process.config.state_file = (
        "state/test.json"
    )

    mock_manager.get.return_value = process

    mock_load_state.return_value = None

    response = client.get(
        "/api/automations/test-automation/state"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "No automation state available yet."
    }


@patch("api.automation_manager")
def test_automation_state_returns_404_for_unknown_automation(
    mock_manager,
):
    mock_manager.get.side_effect = KeyError(
        "Automation 'missing' not found"
    )

    response = client.get(
        "/api/automations/missing/state"
    )

    assert response.status_code == 404


# ============================================================
# POST /api/internal/automation/state
# ============================================================


@patch("api.event_manager")
def test_automation_state_update(
    mock_events,
):
    mock_events.broadcast = AsyncMock()

    state = {
        "automationId": "test-automation",
        "credits": 123,
    }

    response = client.post(
        "/api/internal/automation/state",
        json=state,
    )

    assert response.status_code == 200

    assert response.json() == {
        "received": True
    }

    mock_events.broadcast.assert_awaited_once_with(
        "automation_state",
        state,
    )


# ============================================================
# POST /api/events/test
# ============================================================


@patch("api.event_manager")
def test_event(
    mock_events,
):
    mock_events.broadcast = AsyncMock()

    response = client.post(
        "/api/events/test"
    )

    assert response.status_code == 200

    assert response.json() == {
        "sent": True
    }

    mock_events.broadcast.assert_awaited_once_with(
        "test",
        {
            "message": "SSE is working!"
        },
    )