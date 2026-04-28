from dataclasses import dataclass
from typing import Callable

from .config import TaskLatticeConfig


@dataclass
class Task:
    name: str
    func: Callable
    is_async: bool


class TaskInstance:
    def __init__(
        self, task_name: str, config: TaskLatticeConfig, args: list, kwargs: dict
    ) -> None:
        self.task_name = task_name
        self.args = args
        self.kwargs = kwargs

        self.priority = 2
        self.topic = "tasks/default"

    @property
    def message(self) -> dict:
        return {"task_name": self.task_name, "args": self.args, "kwargs": self.kwargs}
