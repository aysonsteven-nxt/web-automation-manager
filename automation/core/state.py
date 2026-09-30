import json
from pathlib import Path
from typing import Any


def save_state(
    state_file: Path,
    state: dict[str, Any],
) -> None:
    state_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with state_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            state,
            file,
            indent=2,
        )


def load_state(
    state_file: Path,
) -> dict[str, Any] | None:
    if not state_file.exists():
        return None

    try:
        with state_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return None