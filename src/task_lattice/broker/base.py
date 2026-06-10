import logging
import time
from abc import ABC, abstractmethod
from typing import Callable

from task_lattice.config import BrokerConnectionConfig, QueueConfig
from task_lattice.task import TaskInstance

log = logging.getLogger("task-lattice")


class Broker(ABC):
    def __init__(self, connection_details):
        self.connection_details = connection_details

    @abstractmethod
    def connect(self): ...

    @abstractmethod
    def disconnect(self): ...

    @abstractmethod
    def publish(self, task: TaskInstance, queue: QueueConfig): ...

    @abstractmethod
    def start_consumer(self, queue: QueueConfig, handler: Callable[[dict], None]): ...

    def connect_with_retry(self, config: BrokerConnectionConfig):
        """Connect to the broker with exponential backoff retry."""
        log.info("Connecting to the broker...")
        attempt = 0
        max_label = str(config.max_retries) if config.max_retries != -1 else "∞"

        while True:
            try:
                self.connect()
                if attempt > 0:
                    log.info(f"Broker connected after {attempt + 1} attempt(s)")
                return
            except Exception as exc:
                attempt += 1

                if config.max_retries != -1 and attempt > config.max_retries:
                    log.error(f"Failed to connect to broker after {attempt} attempt(s)")
                    exit(1)

                backoff = min(
                    config.backoff_base * (2 ** (attempt - 1)), config.backoff_max
                )
                log.warning(
                    f"Broker connection failed (attempt {attempt}/{max_label}), retrying in {backoff:.1f}s — {exc}"
                )
                time.sleep(backoff)
