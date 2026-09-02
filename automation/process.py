import subprocess
import sys
from pathlib import Path

import psutil

from automation.config import AutomationConfig


BASE_DIR = Path(__file__).resolve().parent.parent
WORKER_SCRIPT = BASE_DIR / "run_automation.py"


class AutomationProcess:
    def __init__(
        self,
        config: AutomationConfig,
    ) -> None:
        self.config = config
        self.process: subprocess.Popen | None = None
        self.log_file = None

    @property
    def automation_id(self) -> str:
        return self.config.id

    def is_running(self) -> bool:
        process = self.process

        return (
            process is not None
            and process.poll() is None
        )

    def start(self) -> bool:
        if self.is_running():
            return False

        if not WORKER_SCRIPT.exists():
            raise FileNotFoundError(
                f"Worker script not found: "
                f"{WORKER_SCRIPT}"
            )

        log_file_path = (
            BASE_DIR / self.config.log_file
        )

        log_file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.log_file = open(
            log_file_path,
            "a",
            encoding="utf-8",
        )

        self.process = subprocess.Popen(
            [
                sys.executable,
                str(WORKER_SCRIPT),
                "--automation-id",
                self.config.id,
            ],
            cwd=BASE_DIR,
            stdout=self.log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

        return True

    def stop(self) -> bool:
        process = self.process

        if process is None or process.poll() is not None:
            self._cleanup()
            return False

        process.terminate()

        try:
            process.wait(
                timeout=5
            )

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

        self.process = None
        self._cleanup_log()

        return True

    def status(self) -> dict:
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

    def find_worker_processes(
        self,
    ) -> list[psutil.Process]:
        workers: list[psutil.Process] = []

        target_script = str(
            WORKER_SCRIPT.resolve()
        ).lower()

        target_automation = (
            f"--automation-id {self.config.id}"
        ).lower()

        candidates: list[
            psutil.Process
        ] = []

        for process in psutil.process_iter(
            ["pid", "cmdline"]
        ):
            try:
                cmdline = process.info[
                    "cmdline"
                ]

                if not cmdline:
                    continue

                command = " ".join(
                    cmdline
                ).lower()

                if (
                    target_script in command
                    and target_automation in command
                ):
                    candidates.append(process)

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
            ):
                continue

        candidate_pids = {
            process.pid
            for process in candidates
        }

        for process in candidates:
            try:
                has_matching_child = any(
                    child.pid in candidate_pids
                    for child in process.children()
                )

                if not has_matching_child:
                    workers.append(process)

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
            ):
                continue

        return workers

    def get_worker_pids(self) -> list[int]:
        return [
            process.pid
            for process in self.find_worker_processes()
        ]

    def stop_all(self) -> list[int]:
        workers = (
            self.find_worker_processes()
        )

        stopped_pids: list[int] = []

        for process in workers:
            try:
                pid = process.pid

                process.terminate()

                try:
                    process.wait(
                        timeout=5
                    )

                except psutil.TimeoutExpired:
                    process.kill()
                    process.wait(
                        timeout=5
                    )

                stopped_pids.append(pid)

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
            ):
                continue

        managed_process = self.process

        if managed_process is not None:
            if (
                managed_process.poll()
                is not None
                or managed_process.pid
                in stopped_pids
            ):
                self.process = None

        self._cleanup_log()

        return stopped_pids

    def _cleanup(self) -> None:
        self.process = None
        self._cleanup_log()

    def _cleanup_log(self) -> None:
        if self.log_file:
            self.log_file.close()
            self.log_file = None