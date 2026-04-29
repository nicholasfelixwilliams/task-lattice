import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from .broker import SolaceBroker

log = logging.getLogger("task-lattice")


class Worker:
    def __init__(self, broker: SolaceBroker, task_registry):
        self._broker = broker
        self._task_registry = task_registry

        self._event_loop = asyncio.new_event_loop()
        self._threadpool = ThreadPoolExecutor()

    def start(self):
        asyncio.set_event_loop(self._event_loop)

        self._broker.start_consumer(self._process_message)

        log.info("Worker started...")

        try:
            self._event_loop.run_forever()
        finally:
            self.shutdown()

    def shutdown(self):
        log.info("Shutting down worker...")
        self._broker.disconnect()
        self._event_loop.stop()
        self._threadpool.shutdown()

    def _process_message(self, message: dict):
        task = self._task_registry.get(message["task_name"])

        if task is None:
            log.warning(f"Unknown task: {message['task_name']}")
            return

        if task.is_async:
            asyncio.run_coroutine_threadsafe(
                task.func(*message["args"], **message["kwargs"]), self._event_loop
            )
        else:
            self._event_loop.run_in_executor(
                self._threadpool,
                lambda: task.func(*message["args"], **message["kwargs"]),
            )
