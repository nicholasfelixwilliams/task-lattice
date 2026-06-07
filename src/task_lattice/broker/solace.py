from functools import cached_property
import json
from typing import Callable
from solace.messaging.messaging_service import MessagingService
from solace.messaging.publisher.persistent_message_publisher import (
    PersistentMessagePublisher,
)
from solace.messaging.receiver.inbound_message import InboundMessage
from solace.messaging.receiver.message_receiver import MessageHandler
from solace.messaging.receiver.persistent_message_receiver import (
    PersistentMessageReceiver,
)
from solace.messaging.resources.queue import Queue
from solace.messaging.resources.topic import Topic

from task_lattice.broker.base import Broker
from task_lattice.config import QueueConfig, SolaceConnectionDetails
from task_lattice.task import TaskInstance


class SolaceBroker(Broker):
    """Broker implementation backed by a Solace PubSub+ event broker."""

    def __init__(self, connection_details: SolaceConnectionDetails):
        super().__init__(connection_details)

        config = {
            "solace.messaging.transport.host": (
                f"tcp://{connection_details.host}:{connection_details.port}"
            ),
            "solace.messaging.service.vpn-name": connection_details.vpn,
            "solace.messaging.authentication.scheme.basic.username": connection_details.username,
            "solace.messaging.authentication.scheme.basic.password": connection_details.password,
        }

        self.service = MessagingService.builder().from_properties(config).build()
        self._receivers: dict[str, PersistentMessageReceiver] = {}

    def connect(self):
        if not self.service.is_connected:
            self.service.connect()

    def disconnect(self):
        """Terminate all receivers and the publisher, then disconnect the service."""
        for receiver in self._receivers.values():
            receiver.terminate()
        self._receivers.clear()

        if "publisher" in self.__dict__:
            self.publisher.terminate()

        if self.service.is_connected:
            self.service.disconnect()

    def publish(self, task: TaskInstance, queue: QueueConfig):
        msg = (
            self.service.message_builder()
            .with_priority(task.priority)
            .build(json.dumps(task.message))
        )
        self.publisher.publish_await_acknowledgement(msg, Topic.of(queue.topic))

    def start_consumer(self, queue: QueueConfig, handler: Callable[[dict], None]):
        receiver = self._get_receiver(queue.queue)

        class _Handler(MessageHandler):
            def on_message(self, message: InboundMessage) -> None:
                payload = message.get_payload_as_string()
                handler(json.loads(payload))
                receiver.ack(message)

        receiver.receive_async(_Handler())

    @cached_property
    def publisher(self) -> PersistentMessagePublisher:
        self.connect()
        publisher = self.service.create_persistent_message_publisher_builder().build()
        publisher.start()
        return publisher

    def _get_receiver(self, queue_name: str) -> PersistentMessageReceiver:
        """Return a started receiver for *queue_name*, creating one if needed."""
        if queue_name not in self._receivers:
            receiver = self.service.create_persistent_message_receiver_builder().build(
                Queue.durable_exclusive_queue(queue_name)
            )
            receiver.start()
            self._receivers[queue_name] = receiver
        return self._receivers[queue_name]
