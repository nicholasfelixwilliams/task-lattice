from functools import cached_property
import json
from solace.messaging.messaging_service import MessagingService
from solace.messaging.receiver.inbound_message import InboundMessage
from solace.messaging.receiver.message_receiver import MessageHandler
from solace.messaging.resources.topic import Topic
from solace.messaging.resources.queue import Queue
from solace.messaging.publisher.persistent_message_publisher import (
    PersistentMessagePublisher,
)

from .config import SolaceConnectionDetails
from .task import TaskInstance


class SolaceBroker:
    def __init__(self, connection_details: SolaceConnectionDetails):
        config = {
            "solace.messaging.transport.host": f"tcp://{connection_details.host}:{connection_details.port}",
            "solace.messaging.service.vpn-name": connection_details.vpn,
            "solace.messaging.authentication.scheme.basic.username": connection_details.username,
            "solace.messaging.authentication.scheme.basic.password": connection_details.password,
        }

        self.service = MessagingService.builder().from_properties(config).build()

    def ensure_connected(self):
        if not self.service.is_connected:
            self.service.connect()

    @cached_property
    def publisher(self) -> PersistentMessagePublisher:
        self.ensure_connected()

        publisher = self.service.create_persistent_message_publisher_builder().build()
        publisher.start()

        return publisher

    def disconnect(self):
        self.service.disconnect()

    def publish(self, task: TaskInstance):
        self.ensure_connected()

        # Build the message
        msg = (
            self.service.message_builder()
            .with_priority(task.priority)
            .build(json.dumps(task.message))
        )

        # Publish the message
        self.publisher.publish_await_acknowledgement(msg, Topic.of("tasks.default"))

    def start_consumer(self, handler):
        self.ensure_connected()
        receiver = self.service.create_persistent_message_receiver_builder().build(
            Queue.durable_exclusive_queue("task_queue")
        )

        class CusomMessageHandler(MessageHandler):
            def on_message(self, message: InboundMessage):
                payload = message.get_payload_as_string()

                # deserialize
                data = json.loads(payload)

                handler(data)

                receiver.ack(message)

        receiver.start()
        receiver.receive_async(CusomMessageHandler())
