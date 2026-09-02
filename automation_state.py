import json
import os
import tempfile
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

    fd, temp_path = tempfile.mkstemp(
        dir=state_file.parent,
        prefix=f"{state_file.stem}_",
        suffix=".tmp",
        text=True,
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                state,
                file,
                indent=2,
            )

        os.replace(
            temp_path,
            state_file,
        )

    except Exception:
        try:
            os.remove(temp_path)
        except OSError:
            pass

        raise


def load_state(
    state_file: Path,
) -> dict[str, Any] | None:
    if not state_file.exists():
        return None

    with state_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)