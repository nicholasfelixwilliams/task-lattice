from inspect import iscoroutinefunction
import logging
from typing import Callable

from .broker import SolaceBroker
from .config import SolaceConnectionDetails, TaskLatticeConfig
from .task import Task, TaskInstance
from .worker import Worker

log = logging.getLogger(__name__)


class TaskLattice:
    _task_registry: dict[str, Task]

    def __init__(
        self, connection_details: SolaceConnectionDetails, config: TaskLatticeConfig
    ):
        self.config = config
        self.broker = SolaceBroker(connection_details)

        self._task_registry = {}

    def close(self):
        self.broker.disconnect()

    def task(self, f: Callable | None = None, *, name: str | None = None):
        """Decorator to register a python function as a TaskLattice task.

        This must be applied to every task (sync or async) in the following way:

            app = TaskLattice(...)

            @app.task
            def function(): ...

            @app.task()
            def function(): ...
        """

        def decorator(func: Callable):
            task_name = name or func.__name__

            if task_name in self._task_registry:
                raise ValueError(f"Task {task_name} is already registered")

            task = Task(name=task_name, func=func, is_async=iscoroutinefunction(func))

            self._task_registry[task.name] = task

            # Attach TaskLattice methods
            def create_task_instance(
                args: list | None = None, kwargs: dict | None = None
            ):
                return TaskInstance(task.name, self.config, args or [], kwargs or {})

            func.create = create_task_instance

            return func

        if f is not None:
            return decorator(f)

        return decorator

    def enqueue(self, task: TaskInstance):
        self.broker.publish(task)

    def start_worker(self):
        worker = Worker(self.broker, self._task_registry)
        worker.start()
