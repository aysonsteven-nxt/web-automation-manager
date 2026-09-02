from automation.config_loader import AutomationConfigLoader
from automation.process import AutomationProcess


class AutomationManager:

    def __init__(self):
        self.processes: dict[str, AutomationProcess] = {}

        self._load_automations()

    def _load_automations(self):
        configs = AutomationConfigLoader.load_all()

        for config in configs:
            self.processes[config.id] = AutomationProcess(config)

    def get(self, automation_id: str) -> AutomationProcess:
        process = self.processes.get(automation_id)

        if process is None:
            raise KeyError(
                f"Automation '{automation_id}' not found"
            )

        return process

    def list(self) -> list[AutomationProcess]:
        return list(self.processes.values())

    def start(self, automation_id: str):
        process = self.get(automation_id)

        if not process.config.enabled:
            raise ValueError(
                f"Automation '{automation_id}' is disabled"
            )

        return process.start()

    def stop(self, automation_id: str):
        return self.get(automation_id).stop()

    def stop_all(self, automation_id: str):
        return self.get(automation_id).stop_all()

    def status(self, automation_id: str):
        return self.get(automation_id).status()

    def pids(self, automation_id: str):
        return self.get(automation_id).get_worker_pids()


# Global manager instance used by FastAPI
automation_manager = AutomationManager()