import asyncio
from contextlib import AsyncExitStack, contextmanager
from functools import partial
import logging
import signal
import sys
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
    log.info(f"Task {task.name} completed in {end_ts - start_ts:.5f} seconds")


class Worker:
    """Class encapsulating a single worker process.

    This includes how the process starts up, shuts down and handles tasks.
    """

    def __init__(
        self,
        broker: SolaceBroker,
        task_registry,
        target_queues: list[QueueConfig],
        max_concurrency: int | None = None,
        shutdown_grace_period: int | None = None,
        worker_lifecycle=None,
    ):
        self._broker = broker
        self._task_registry = task_registry
        self._target_queues = target_queues
        self._max_concurrency = max_concurrency or 100
        self._shutdown_grace_period = shutdown_grace_period or 30
        self._worker_lifecycle = worker_lifecycle
        self._active = False

        # Configure event loop for tasks
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)
        self._active_tasks: set[asyncio.Task] = set()

        # Configure semaphore for controlling concurrency
        self._concurrency_semaphore = asyncio.Semaphore(self._max_concurrency)

    def start(self):
        """Entrypoint for a worker"""
        self._active = True

        self._event_loop.create_task(self._start())
        self._event_loop.run_forever()

    async def _start(self):
        async with AsyncExitStack() as stack:
            # Configure worker lifecycling
            if self._worker_lifecycle:
                lifecycle_instance = self._worker_lifecycle

                if hasattr(lifecycle_instance, "__aenter__"):
                    await stack.enter_async_context(lifecycle_instance)
                else:
                    stack.enter_context(lifecycle_instance)

            log.info(f"Maximum Concurrency: {self._max_concurrency}")
            log.info(f"Tasks Registered: {len(self._task_registry)}")

            log.info("Listening to Queues:")
            for queue in self._target_queues:
                log.info(
                    f"\t- {queue.name}  [topic={queue.topic}] [queue={queue.queue}]"
                )
                self._broker.start_consumer(queue, self._process_message)

            self._configure_signals()

            log.info("Worker started...")

    def _configure_signals(self):
        """Add listeners to kill and term signals to gracefully shut down worker"""
        if sys.platform == "win32":

            def handler(*_):
                asyncio.run_coroutine_threadsafe(
                    self.shutdown(),
                    self._event_loop,
                )

            signal.signal(signal.SIGINT, handler)
            signal.signal(signal.SIGTERM, handler)
        else:
            for sig in (signal.SIGINT, signal.SIGTERM):
                self._event_loop.add_signal_handler(
                    sig, lambda s=sig: asyncio.create_task(self.shutdown())
                )

    async def shutdown(self):
        """Exitpoint for a worker. Cleanly shuts down worker"""
        if not self._active:
            return

        log.info("Shutting down worker...")
        self._active = False

        # Stop listening for new messages
        self._broker.disconnect()

        if self._active_tasks:
            log.info(f"Waiting for {len(self._active_tasks)} task to complete...")
            _, pending = await asyncio.wait(
                self._active_tasks, timeout=self._shutdown_grace_period
            )

            if pending:
                log.warning(f"{len(pending)} tasks could not be completed in time")

        self._event_loop.stop()
        log.info("Worker shut down...")

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
            self._schedule_task(task, message["args"], message["kwargs"]),
            self._event_loop,
        )

    async def _schedule_task(self, task: TaskDefinition, args: list, kwargs: dict):
        """This method is to add the task to the event loop with tracking.

        This includes ensuring concurrency capacity within the worker.
        """
        async_task = self._event_loop.create_task(
            self._process_task(task, args, kwargs)
        )

        self._active_tasks.add(async_task)

        async_task.add_done_callback(self._active_tasks.discard)

    async def _process_task(self, task: TaskDefinition, args: list, kwargs: dict):
        """Task processing wrapper.

        This including task concurrency, logging, timing, dependency resolution, ....
        """
        async with self._concurrency_semaphore:
            with timer(task):
                resolved_kwargs, stack = await resolve_dependencies(task.func, kwargs)

                if task.lifeycle:
                    if hasattr(task.lifeycle, "__aenter__"):
                        await stack.enter_async_context(task.lifeycle)  # type: ignore
                    else:
                        stack.enter_context(task.lifeycle)  # type: ignore

                async with stack:
                    if task.is_async:
                        await task.func(*args, **resolved_kwargs)
                    else:
                        func = partial(task.func, *args, **resolved_kwargs)
                        await asyncio.to_thread(func)
