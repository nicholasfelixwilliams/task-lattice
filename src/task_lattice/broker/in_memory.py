from collections import defaultdict
import json
from queue import PriorityQueue

from task_lattice.broker.base import Broker
from task_lattice.config import QueueConfig
from task_lattice.task import TaskInstance


class InMemoryBroker(Broker):
    """Simple in memory broker that uses python's in built priority queue.

    This supports single concurrency execution only and offers no persistence.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create the in memory queues
        self.queues: dict[str, PriorityQueue] = defaultdict(lambda: PriorityQueue())

    def connect(self):
        pass  # No connection needed

    def disconnect(self):
        pass  # No connection needed

    def publish(self, task: TaskInstance, queue: QueueConfig):
        q = self.queues[queue.name]
        message = json.dumps(task.message)

        q.put((task.priority, message))

    def start_consumer(self, queue: QueueConfig, handler):
        q = self.queues[queue.name]

        while True:
            payload = q.get()
            message = json.loads(payload)

            handler(message)
            q.task_done()
