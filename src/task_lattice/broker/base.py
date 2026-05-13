from abc import ABC, abstractmethod

from task_lattice.config import QueueConfig
from task_lattice.task import TaskInstance


class Broker(ABC):
    def __init__(self, connection_details):
        self.connection_details = connection_details

    @abstractmethod
    def connect(self):
        """Connect to the broker"""
        ...

    @abstractmethod
    def disconnect(self):
        """Disconnect from the broker"""
        ...

    @abstractmethod
    def publish(self, task: TaskInstance, queue: QueueConfig):
        """Publish a new message to a specific queue on the broker"""
        ...

    @abstractmethod
    def start_consumer(self, queue: QueueConfig, handler):
        """Start consuming messages from a specific queue.

        Will call the handler function for each message.
        """
        ...
