import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import logging
import time
import threading

from .broker import SolaceBroker
from .config import QueueConfig
from .task import Task

log = logging.getLogger("task-lattice")


@contextmanager
def timer(task: Task):
    """Context manager to time task and log time taken."""
    start_ts = time.perf_counter()

    yield

    end_ts = time.perf_counter()
    log.info(f"Task {task.name} completed in {end_ts - start_ts: .5f} seconds")


def sync_wrapper(task: Task, args: list, kwargs: dict):
    with timer(task):
        task.func(*args, **kwargs)


async def async_wrapper(task: Task, args: list, kwargs: dict):
    with timer(task):
        await task.func(*args, **kwargs)


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
        self._target_queues = target_queues  # TODO: Implement usage
        self._max_concurrency = max_concurrency
        self._worker_lifecycle = worker_lifecycle  # TODO: Implement usage
        self._task_lifecycle = task_lifecycle  # TODO: Implement usage

        # Configure event loop for async tasks
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)

        # Configure threadpool for sync tasks
        self._threadpool = ThreadPoolExecutor()

        # Configure semaphore for controlling concurrency
        self._concurrency_semaphore = threading.Semaphore(self._max_concurrency)

    def start(self):
        """Entrypoint for a worker. Subscribes to the broker for incomming messages"""
        log.info(f"Maximum Concurrency: {self._max_concurrency}")
        log.info("Listening to Queues:")
        for queue in self._target_queues:
            log.info(f"\t- {queue.name} ({queue.topic})")
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
        self._threadpool.shutdown()

    def _process_message(self, message: dict):
        """Task execution wrapper.

        Inputs:
            - message from broker
        """
        task = self._task_registry.get(message["task_name"])

        if task is None:
            log.warning(f"Unknown task: {message['task_name']}")
            return

        # Ensure concurrency capacity
        with self._concurrency_semaphore:
            if task.is_async:
                asyncio.run_coroutine_threadsafe(
                    async_wrapper(task, message["args"], message["kwargs"]),
                    self._event_loop,
                )
            else:
                self._event_loop.run_in_executor(
                    self._threadpool,
                    lambda: sync_wrapper(task, message["args"], message["kwargs"]),
                )
