import logging
from inspect import iscoroutinefunction
from typing import Callable, overload

from .broker import BROKERS
from .config import ConnectionDetails, TaskLatticeConfig
from .task import TaskDefinition, TaskFunction, TaskInstance
from .worker import Worker

log = logging.getLogger("task-lattice")


class TaskLattice:
    _task_registry: dict[str, TaskDefinition]

    def __init__(
        self,
        connection_details: ConnectionDetails,
        config: TaskLatticeConfig,
    ):
        self.config = config

        if connection_details.broker not in BROKERS:
            raise ValueError(
                f"Unknown broker '{connection_details.broker}'. Valid options: {list(BROKERS.keys())}"
            )

        self._connection_details = connection_details
        self.broker = BROKERS[connection_details.broker](connection_details.config)
        self._task_registry = {}

    def close(self):
        """Disconnect from the broker"""
        self.broker.disconnect()

    @overload
    def task(
        self, f: Callable, *, name: str | None = None, lifecycle=None, retry=None
    ) -> TaskFunction: ...

    @overload
    def task(
        self, f: None = None, *, name: str | None = None, lifecycle=None, retry=None
    ) -> Callable[[Callable], TaskFunction]: ...

    def task(  # type: ignore[misc]
        self,
        f: Callable | None = None,
        *,
        name: str | None = None,
        lifecycle=None,
        retry=None,
    ):
        """Decorator to register a Python function as a Task Lattice task.

        Sample usage:

            @app.task
            def my_task(): ...

            @app.task(name="custom.name", ...)
            async def my_task(): ...
        """

        def decorator(func: Callable) -> TaskFunction:
            task_name = name or func.__name__

            if task_name in self._task_registry:
                raise ValueError(f"Task '{task_name}' is already registered")

            task_def = TaskDefinition(
                name=task_name,
                func=func,
                is_async=iscoroutinefunction(func),
                lifecycle=lifecycle,
                retry=retry,
            )
            self._task_registry[task_def.name] = task_def

            return TaskFunction(func, task_def, self.config)

        if f is not None:
            return decorator(f)

        return decorator

    def enqueue(self, task: TaskInstance, queue: str | None = None):
        """Add a task for execution by a worker."""
        queue_name = queue or self.config.default_queue
        queue_config = next(
            (q for q in self.config.queues if q.name == queue_name), None
        )
        if queue_config is None:
            raise ValueError(
                f"Queue '{queue_name}' is not configured. Available queues: {[q.name for q in self.config.queues]}"
            )

        task.queue = queue_name
        self.broker.publish(task, queue_config)

    def enqueue_all(self, *tasks: TaskInstance, queue: str | None = None):
        """Add all tasks for execution by workers."""
        for task in tasks:
            self.enqueue(task, queue)

    def start_worker(
        self,
        queues: list[str] | None = None,
        concurrency: int | None = None,
    ):
        """Start a worker process. Blocks until the worker shuts down."""
        target_queues = (
            [q for q in self.config.queues if q.name in queues]
            if queues
            else self.config.queues
        )

        worker = Worker(
            broker=self.broker,
            task_registry=self._task_registry,
            target_queues=target_queues,
            connection_config=self._connection_details.connection,
            max_concurrency=concurrency or self.config.worker_concurrency,
            shutdown_grace_period=self.config.worker_shutdown_grace_period,
            worker_lifecycle=self.config.worker_lifecycle,
        )
        worker.start()
