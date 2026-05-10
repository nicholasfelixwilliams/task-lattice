import asyncio
from contextlib import contextmanager
from functools import partial
import logging
import time

from .broker import SolaceBroker
from .config import QueueConfig
from .dependency import resolve_dependencies
from .task import TaskDefinition

log = logging.getLogger("task-lattice")


@contextmanager
def timer(task: TaskDefinition):
    """Context manager to time task and log time taken."""
    log.info(f"Task {task.name} started")
    start_ts = time.perf_counter()

    yield

    end_ts = time.perf_counter()
    log.info(f"Task {task.name} completed in {end_ts - start_ts: .5f} seconds")


class Worker:
    """Class encapsulating a single worker process.

    This includes how the process starts up, shuts down and handles tasks.
    """

    def __init__(
        self,
        broker: SolaceBroker,
        task_registry,
        target_queues: list[QueueConfig],
        max_concurrency: int = 100,
        worker_lifecycle=None,
        task_lifecycle=None,
    ):
        self._broker = broker
        self._task_registry = task_registry
        self._target_queues = target_queues
        self._max_concurrency = max_concurrency
        self._worker_lifecycle = worker_lifecycle  # TODO: Implement usage
        self._task_lifecycle = task_lifecycle

        # Configure event loop for tasks
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)
        self._active_tasks: set[asyncio.Task] = set()

        # Configure semaphore for controlling concurrency
        self._concurrency_semaphore = asyncio.Semaphore(self._max_concurrency)

    def start(self):
        """Entrypoint for a worker. Subscribes to the broker for incomming messages"""
        log.info(f"Maximum Concurrency: {self._max_concurrency}")
        log.info("Listening to Queues:")
        for queue in self._target_queues:
            log.info(f"\t- {queue.name}  [topic={queue.topic}] [queue={queue.queue}]")
            self._broker.start_consumer(queue, self._process_message)

        log.info("Worker started...")
        try:
            self._event_loop.run_forever()
        except (Exception, KeyboardInterrupt):
            self.shutdown()

    def shutdown(self):
        """Exitpoint for a worker. Cleanly shuts down worker"""
        log.info("Shutting down worker...")
        self._broker.disconnect()
        self._event_loop.stop()

    def _process_message(self, message: dict):
        """Task execution wrapper.

        Inputs:
            - message from broker
        """
        task = self._task_registry.get(message["task_name"])

        if task is None:
            log.warning(f"Unknown task: {message['task_name']}")
            return

        asyncio.run_coroutine_threadsafe(
            self.process_task(task, message["args"], message["kwargs"]),
            self._event_loop,
        )

    async def process_task(self, task: TaskDefinition, args: list, kwargs: dict):
        # Ensure concurrency capacity
        async with self._concurrency_semaphore:
            with timer(task):
                resolved_kwargs, stack = await resolve_dependencies(task.func, kwargs)

                if self._task_lifecycle:
                    if hasattr(self._task_lifecycle, "__aenter__"):
                        await stack.enter_async_context(self._task_lifecycle)
                    else:
                        stack.enter_context(self._task_lifecycle)

                async with stack:
                    if task.is_async:
                        await task.func(*args, **resolved_kwargs)
                    else:
                        func = partial(task.func, *args, **resolved_kwargs)
                        await asyncio.to_thread(func)
