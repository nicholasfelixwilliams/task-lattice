import asyncio
from contextlib import AsyncExitStack, contextmanager
from functools import partial
import logging
import signal
import sys
import time

from .broker import Broker
from .config import BrokerConnectionConfig, QueueConfig
from .dependency import resolve_dependencies
from .task import TaskDefinition, TaskInstance

log = logging.getLogger("task-lattice")


@contextmanager
def _task_timer(name: str, attempt: int, max_retries: int):
    log.info(f"Task '{name}' started")
    start = time.perf_counter()
    failed = False
    try:
        yield
    except Exception:
        failed = True
        raise
    finally:
        elapsed = time.perf_counter() - start
        if failed:
            log.info(f"Task '{name}' failed after {elapsed:.5f}s")
        else:
            log.info(f"Task '{name}' completed in {elapsed:.5f}s")


class Worker:
    def __init__(
        self,
        broker: Broker,
        task_registry: dict[str, TaskDefinition],
        target_queues: list[QueueConfig],
        connection_config: BrokerConnectionConfig,
        max_concurrency: int | None = None,
        shutdown_grace_period: int | None = None,
        worker_lifecycle=None,
    ):
        self._broker = broker
        self._task_registry = task_registry
        self._target_queues = target_queues
        self._connection_config = connection_config
        self._max_concurrency = max_concurrency or 100
        self._shutdown_grace_period = shutdown_grace_period or 30
        self._worker_lifecycle = worker_lifecycle
        self._active = False

        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)

        self._active_tasks: set[asyncio.Task] = set()
        self._concurrency_semaphore = asyncio.Semaphore(self._max_concurrency)
        self._shutdown_event: asyncio.Event = asyncio.Event()

    def start(self):
        """Start the worker. Blocks until the worker shuts down."""
        self._active = True
        self._event_loop.create_task(self._start())
        self._event_loop.run_forever()

    async def shutdown(self):
        """Gracefully stop the worker."""
        if not self._active:
            return

        self._active = False
        log.info("Shutting down worker...")

        self._broker.disconnect()

        if self._active_tasks:
            log.info(f"Waiting for {len(self._active_tasks)} task(s) to complete...")
            _, pending = await asyncio.wait(
                self._active_tasks, timeout=self._shutdown_grace_period
            )
            if pending:
                log.warning(
                    f"{len(pending)} task(s) did not complete within the {self._shutdown_grace_period}s grace period"
                )

        self._shutdown_event.set()
        log.info("Worker shut down")

    async def _start(self):
        async with AsyncExitStack() as stack:
            if self._worker_lifecycle:
                if hasattr(self._worker_lifecycle, "__aenter__"):
                    await stack.enter_async_context(self._worker_lifecycle)
                else:
                    stack.enter_context(self._worker_lifecycle)

            self._broker.connect_with_retry(self._connection_config)

            log.info(f"Maximum concurrency: {self._max_concurrency}")
            log.info(f"Tasks registered: {len(self._task_registry)}")
            log.info("Listening to queues:")
            for queue in self._target_queues:
                log.info(
                    f"\t- {queue.name}  [topic={queue.topic}] [queue={queue.queue}]"
                )
                self._broker.start_consumer(queue, self._on_message)

            self._configure_signals()
            log.info("Worker started")

            await self._shutdown_event.wait()

        self._event_loop.stop()

    def _configure_signals(self):
        if sys.platform == "win32":

            def handler(*_):
                asyncio.run_coroutine_threadsafe(self.shutdown(), self._event_loop)

            signal.signal(signal.SIGINT, handler)
            signal.signal(signal.SIGTERM, handler)
        else:
            for sig in (signal.SIGINT, signal.SIGTERM):
                self._event_loop.add_signal_handler(
                    sig, lambda: asyncio.create_task(self.shutdown())
                )

    def _on_message(self, message: dict):
        task = self._task_registry.get(message.get("task_name", ""))
        if task is None:
            log.warning(
                f"Received message for unknown task: '{message.get('task_name')}'"
            )
            return

        asyncio.run_coroutine_threadsafe(
            self._schedule_task(task, message),
            self._event_loop,
        )

    async def _schedule_task(self, task: TaskDefinition, message: dict):
        async_task = self._event_loop.create_task(self._run_task(task, message))
        self._active_tasks.add(async_task)
        async_task.add_done_callback(self._active_tasks.discard)

    async def _run_task(self, task: TaskDefinition, message: dict):
        args: list = message.get("args", [])
        kwargs: dict = message.get("kwargs", {})
        attempt: int = message.get("attempt", 0)
        max_retries: int = message.get("max_retries", 0)
        retry_on: tuple[type[BaseException], ...] = TaskInstance.from_message(
            message
        ).retry_on

        async with self._concurrency_semaphore:
            with _task_timer(task.name, attempt, max_retries):
                resolved_kwargs, dep_stack = await resolve_dependencies(
                    task.func, kwargs
                )

                if task.lifecycle:
                    if hasattr(task.lifecycle, "__aenter__"):
                        await dep_stack.enter_async_context(task.lifecycle)
                    else:
                        dep_stack.enter_context(task.lifecycle)

                try:
                    async with dep_stack:
                        if task.is_async:
                            await task.func(*args, **resolved_kwargs)
                        else:
                            await asyncio.to_thread(
                                partial(task.func, *args, **resolved_kwargs)
                            )

                except Exception as exc:
                    should_retry = (
                        max_retries > 0
                        and attempt < max_retries
                        and isinstance(exc, retry_on)
                    )

                    if should_retry:
                        next_attempt = attempt + 1
                        log.debug(
                            f"Task '{task.name}' failed on attempt {next_attempt}/{max_retries + 1} — scheduling retry. {type(exc).__name__}: {exc}"
                        )
                        await self._retry_task(message, next_attempt)
                    else:
                        log.exception(
                            f"Task '{task.name}' raised an unhandled exception (attempt {attempt + 1}/{max_retries + 1})"
                        )

    async def _retry_task(self, message: dict, next_attempt: int):
        queue_name = message.get("queue")
        queue_config = next(
            (q for q in self._target_queues if q.name == queue_name), None
        )
        if queue_config is None:
            log.error(
                f"Cannot retry task '{message.get('task_name')}': queue '{queue_name}' not found in target queues"
            )
            return

        retry_instance = TaskInstance.from_message({**message, "attempt": next_attempt})
        self._broker.publish(retry_instance, queue_config)
