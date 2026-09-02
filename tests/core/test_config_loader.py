import json

import pytest

from automation.core.config_loader import (
    AutomationConfigLoader,
)


def write_config(
    tmp_path,
    automations,
):
    config_file = (
        tmp_path / "automations.json"
    )

    config_file.write_text(
        json.dumps(
            {
                "automations": automations,
            }
        ),
        encoding="utf-8",
    )

    return config_file


def automation_data(
    automation_id="test",
    name="Test Automation",
    automation_type="web",
    strategy="voting",
):
    return {
        "id": automation_id,
        "name": name,
        "type": automation_type,
        "strategy": strategy,
        "config": {
            "web": {
                "url": "https://example.com",
                "session_file": "test_session.json",
            },
            "strategy": {
                "action_delay_seconds": 3,
            },
        },
        "state_file": "state/test.json",
        "log_file": "logs/test.log",
        "check_interval_seconds": 60,
        "enabled": True,
    }


def test_load_all(tmp_path):
    config_file = write_config(
        tmp_path,
        [
            automation_data(),
        ],
    )

    AutomationConfigLoader.CONFIG_FILE = (
        config_file
    )

    configs = AutomationConfigLoader.load_all()

    assert len(configs) == 1

    config = configs[0]

    assert config.id == "test"
    assert config.name == "Test Automation"
    assert config.type == "web"
    assert config.strategy == "voting"

    assert config.config == {
        "web": {
            "url": "https://example.com",
            "session_file": "test_session.json",
        },
        "strategy": {
            "action_delay_seconds": 3,
        },
    }

    assert (
        config.config["web"]["url"]
        == "https://example.com"
    )

    assert (
        config.config["web"]["session_file"]
        == "test_session.json"
    )

    assert (
        config.config["strategy"][
            "action_delay_seconds"
        ]
        == 3
    )

    assert config.state_file == "state/test.json"
    assert config.log_file == "logs/test.log"
    assert config.check_interval_seconds == 60
    assert config.enabled is True


def test_load_all_multiple_automations(
    tmp_path,
):
    config_file = write_config(
        tmp_path,
        [
            automation_data(
                automation_id="automation-1",
            ),
            automation_data(
                automation_id="automation-2",
                name="Second Automation",
            ),
        ],
    )

    AutomationConfigLoader.CONFIG_FILE = (
        config_file
    )

    configs = AutomationConfigLoader.load_all()

    assert len(configs) == 2

    assert configs[0].id == "automation-1"

    assert configs[1].id == "automation-2"
    assert configs[1].name == "Second Automation"


def test_load_by_id(tmp_path):
    config_file = write_config(
        tmp_path,
        [
            automation_data(
                automation_id="forsaken-ro",
                name="ForsakenRO",
            ),
            automation_data(
                automation_id="other",
                name="Other Automation",
            ),
        ],
    )

    AutomationConfigLoader.CONFIG_FILE = (
        config_file
    )

    config = (
        AutomationConfigLoader.load_by_id(
            "forsaken-ro"
        )
    )

    assert config.id == "forsaken-ro"
    assert config.name == "ForsakenRO"


def test_load_by_id_unknown_automation(
    tmp_path,
):
    config_file = write_config(
        tmp_path,
        [
            automation_data(),
        ],
    )

    AutomationConfigLoader.CONFIG_FILE = (
        config_file
    )

    with pytest.raises(
        ValueError,
        match="Automation 'unknown' not found",
    ):
        AutomationConfigLoader.load_by_id(
            "unknown"
        )


def test_load_all_missing_config_file(
    tmp_path,
):
    config_file = (
        tmp_path / "missing.json"
    )

    AutomationConfigLoader.CONFIG_FILE = (
        config_file
    )

    with pytest.raises(
        FileNotFoundError,
        match="Automation configuration not found",
    ):
        AutomationConfigLoader.load_all()


def test_load_all_missing_automations_property(
    tmp_path,
):
    config_file = (
        tmp_path / "automations.json"
    )

    config_file.write_text(
        json.dumps(
            {
                "somethingElse": []
            }
        ),
        encoding="utf-8",
    )

    AutomationConfigLoader.CONFIG_FILE = (
        config_file
    )

    with pytest.raises(
        ValueError,
        match="Missing 'automations' property",
    ):
        AutomationConfigLoader.load_all()


def test_load_all_automations_not_list(
    tmp_path,
):
    config_file = (
        tmp_path / "automations.json"
    )

    config_file.write_text(
        json.dumps(
            {
                "automations": {}
            }
        ),
        encoding="utf-8",
    )

    AutomationConfigLoader.CONFIG_FILE = (
        config_file
    )

    with pytest.raises(
        ValueError,
        match="'automations' must be an array",
    ):
        AutomationConfigLoader.load_all()