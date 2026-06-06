from collections import defaultdict
import json
import threading
from typing import Callable
from queue import Empty, PriorityQueue

from task_lattice.broker.base import Broker
from task_lattice.config import QueueConfig
from task_lattice.task import TaskInstance


class InMemoryBroker(Broker):
    """Simple in memory broker that uses python's in built priority queue.

    This supports single concurrency execution only and offers no persistence.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._queues: dict[str, PriorityQueue] = defaultdict(PriorityQueue)
        self._stop_event = threading.Event()
        self._consumer_threads: list[threading.Thread] = []

    def connect(self):
        self._stop_event.clear()

    def disconnect(self):
        self._stop_event.set()
        for thread in self._consumer_threads:
            thread.join(timeout=1)
        self._consumer_threads.clear()

    def publish(self, task: TaskInstance, queue: QueueConfig):
        self._queues[queue.name].put((task.priority, json.dumps(task.message)))

    def start_consumer(self, queue: QueueConfig, handler: Callable[[dict], None]):
        q = self._queues[queue.name]

        def _consume():
            while not self._stop_event.is_set():
                try:
                    _, payload = q.get(timeout=0.1)
                    handler(json.loads(payload))
                    q.task_done()
                except Empty:
                    continue

        thread = threading.Thread(
            target=_consume, daemon=True, name=f"consumer-{queue.name}"
        )
        thread.start()
        self._consumer_threads.append(thread)
