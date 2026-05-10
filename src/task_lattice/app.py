from inspect import iscoroutinefunction
import logging
from typing import Callable, overload

from .broker import SolaceBroker
from .config import SolaceConnectionDetails, TaskLatticeConfig
from .task import TaskDefinition, TaskFunction, TaskInstance
from .worker import Worker

log = logging.getLogger(__name__)


class TaskLattice:
    _task_registry: dict[str, TaskDefinition]

    def __init__(
        self, connection_details: SolaceConnectionDetails, config: TaskLatticeConfig
    ):
        self.config = config
        self.broker = SolaceBroker(connection_details)

        self._task_registry = {}

    def close(self):
        self.broker.disconnect()

    """Task Registration"""

    @overload
    def task(
        self,
        f: Callable,
        *,
        name: str | None = None,
        lifecycle=None
    ) -> TaskFunction: ...

    @overload
    def task(
        self,
        f: None = None,
        *,
        name: str | None = None,
        lifecycle=None
    ) -> Callable[[Callable], TaskFunction]: ...

    def task( # type: ignore
        self, f: Callable | None = None, *, name: str | None = None, lifecycle=None
    ):
        """Decorator to register a python function as a TaskLattice task.

        This must be applied to every task (sync or async) in the following way:

            app = TaskLattice(...)

            @app.task
            def function(): ...

            @app.task()
            def function(): ...
        """

        def decorator(func: Callable) -> TaskFunction:
            task_name = name or func.__name__

            if task_name in self._task_registry:
                raise ValueError(f"Task {task_name} is already registered")

            task = TaskDefinition(
                name=task_name,
                func=func,
                is_async=iscoroutinefunction(func),
                lifeycle=lifecycle,
            )

            self._task_registry[task.name] = task

            # Build TaskFunction object to return
            return TaskFunction(func, task, self.config)

        if f is not None:
            return decorator(f)

        return decorator

    """Task Execution"""

    def enqueue(self, task: TaskInstance, queue: str | None = None):
        """Enqueues a task to be executed by a worker."""
        queue = queue or self.config.default_queue
        queue_config = next(q for q in self.config.queues if q.name == queue)
        self.broker.publish(task, queue_config)

    """Worker"""

    def start_worker(
        self, queues: list[str] | None = None, concurrency: int | None = None
    ):
        """Starts a worker.

        This will run until manually stopped.
        """
        # If no queues are given, target all
        target_queues = (
            [q for q in self.config.queues if q.name in queues]
            if queues
            else self.config.queues
        )
        worker = Worker(
            self.broker,
            self._task_registry,
            target_queues=target_queues,
            max_concurrency=concurrency or self.config.worker_concurrency,
            shutdown_grace_period=self.config.worker_shutdown_grace_period,
            worker_lifecycle=self.config.worker_lifecycle,
        )
        worker.start()
