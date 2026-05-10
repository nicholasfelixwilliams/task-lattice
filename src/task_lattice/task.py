from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, ContextManager, AsyncContextManager

from .config import TaskLatticeConfig


@dataclass
class TaskDefinition:
    """Key information on a task definition.

    This is stored in the app's task registry and used when
    creating a task instance.
    """

    name: str
    func: Callable
    is_async: bool
    lifeycle: AsyncContextManager | ContextManager | None = None


class TaskInstance:
    """An instance of a specific class.

    This represents a call to a specific python function which is due to
    be executed on a worker process.
    """

    def __init__(
        self, task_name: str, config: TaskLatticeConfig, args: list, kwargs: dict
    ) -> None:
        self.task_name = task_name
        self.args = args
        self.kwargs = kwargs

        self.priority = 2

    @property
    def message(self) -> dict:
        return {
            "task_name": self.task_name,
            "args": self.args,
            "kwargs": self.kwargs,
            "creation_timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }


class TaskFunction:
    """Wrapper class for a python function representing a task.

    Using the "@app.task" decorator will wrap the function in a "TaskFunction" class.
    This gives additional functionality including:
        - Simple creation of "TaskInstance" objects
    """

    def __init__(
        self, func: Callable, task_def: TaskDefinition, config: TaskLatticeConfig
    ):
        self.func = func
        self.task_def = task_def
        self.config = config

    def create(
        self, args: list | None = None, kwargs: dict | None = None
    ) -> TaskInstance:
        return TaskInstance(self.task_def.name, self.config, args or [], kwargs or {})

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
