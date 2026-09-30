import subprocess
import sys
from pathlib import Path

from automation.core.config import AutomationConfig


class AutomationProcess:
    """
    Manages the worker subprocess for an automation.

    This class is responsible only for process lifecycle:
    - Starting the worker
    - Checking process status
    - Stopping the worker
    - Tracking the worker PID
    """

    WORKER_SCRIPT = (
        Path(__file__).resolve().parent.parent.parent
        / "run_automation.py"
    )

    def __init__(
        self,
        config: AutomationConfig,
    ):
        self.config = config
        self.process: subprocess.Popen | None = None

    def start(self) -> bool:
        """
        Start the automation worker process.

        Returns:
            True if a new process was started.
            False if the automation was already running.
        """

        if self.is_running():
            return False

        self.process = subprocess.Popen(
            [
                sys.executable,
                str(self.WORKER_SCRIPT),
                self.config.id,
            ],
            cwd=(
                Path(__file__)
                .resolve()
                .parent.parent.parent
            ),
        )

        return True

    def stop(self) -> bool:
        """
        Stop the automation worker process.

        Returns:
            True if a process was stopped.
            False if no running process existed.
        """

        if not self.is_running():
            return False

        if self.process is None:
            return False

        self.process.terminate()

        try:
            self.process.wait(
                timeout=10
            )
        except subprocess.TimeoutExpired:
            self.process.kill()

            try:
                self.process.wait(
                    timeout=5
                )
            except subprocess.TimeoutExpired:
                pass

        return True

    def stop_all(self) -> list[int]:
        """
        Stop the automation worker process.

        Returns:
            List containing the stopped PID, if any.
        """

        if not self.is_running():
            return []

        if self.process is None:
            return []

        pid = self.process.pid

        self.stop()

        return [pid]

    def is_running(self) -> bool:
        """
        Return whether the worker process is currently running.
        """

        if self.process is None:
            return False

        return self.process.poll() is None

    def status(self) -> dict:
        """
        Return the current process status.
        """

        running = self.is_running()

        pid = None
        returncode = None

        if self.process is not None:
            pid = self.process.pid

            if not running:
                returncode = self.process.poll()

        return {
            "running": running,
            "pid": pid,
            "returncode": returncode,
        }

    def get_worker_pids(self) -> list[int]:
        """
        Return the PID of the worker process, if running.
        """

        if not self.is_running():
            return []

        if self.process is None:
            return []

        return [
            self.process.pid
        ]