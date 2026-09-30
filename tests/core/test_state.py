import json

from automation.core.state import (
    load_state,
    save_state,
)


def test_save_state(tmp_path):
    state_file = (
        tmp_path / "state" / "test.json"
    )

    state = {
        "automationId": "test",
        "automationName": "Test Automation",
        "running": True,
        "credits": 100,
    }

    save_state(
        state_file,
        state,
    )

    assert state_file.exists()

    saved_data = json.loads(
        state_file.read_text(
            encoding="utf-8"
        )
    )

    assert saved_data == state


def test_save_state_creates_parent_directories(
    tmp_path,
):
    state_file = (
        tmp_path
        / "state"
        / "nested"
        / "test.json"
    )

    state = {
        "status": "running",
    }

    save_state(
        state_file,
        state,
    )

    assert state_file.exists()

    loaded = json.loads(
        state_file.read_text(
            encoding="utf-8"
        )
    )

    assert loaded == state


def test_load_state(tmp_path):
    state_file = (
        tmp_path / "state.json"
    )

    state = {
        "automationId": "forsaken-ro",
        "credits": 250,
        "availableCount": 2,
    }

    state_file.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    result = load_state(
        state_file
    )

    assert result == state


def test_load_state_missing_file(
    tmp_path,
):
    state_file = (
        tmp_path / "missing.json"
    )

    result = load_state(
        state_file
    )

    assert result is None


def test_load_state_invalid_json(
    tmp_path,
):
    state_file = (
        tmp_path / "invalid.json"
    )

    state_file.write_text(
        "{ invalid json",
        encoding="utf-8",
    )

    result = load_state(
        state_file
    )

    assert result is None


def test_load_state_empty_file(
    tmp_path,
):
    state_file = (
        tmp_path / "empty.json"
    )

    state_file.write_text(
        "",
        encoding="utf-8",
    )

    result = load_state(
        state_file
    )

    assert result is None