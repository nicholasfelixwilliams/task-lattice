import json
from solace.messaging.messaging_service import MessagingService
from solace.messaging.receiver.message_receiver import MessageHandler
from solace.messaging.resources.topic import Topic
from solace.messaging.resources.queue import Queue
from solace.messaging.publisher.persistent_message_publisher import (
    PersistentMessagePublisher,
)

from .config import SolaceConnectionDetails
from .task import TaskInstance


class SolaceBroker:
    publisher: PersistentMessagePublisher

    def __init__(self, connection_details: SolaceConnectionDetails):
        self.connection_details = connection_details

        config = {
            "solace.messaging.transport.host": f"tcp://{self.connection_details.host}:{self.connection_details.port}",
            "solace.messaging.service.vpn-name": self.connection_details.vpn,
            "solace.messaging.authentication.scheme.basic.username": self.connection_details.username,
            "solace.messaging.authentication.scheme.basic.password": self.connection_details.password,
        }

        self.service = MessagingService.builder().from_properties(config).build()
        self.publisher = (
            self.service.create_persistent_message_publisher_builder().build()
        )

    def connect(self):
        self.service.connect()
        self.publisher.start()

    def ensure_connected(self):
        if not self.service.is_connected:
            self.service.connect()
        if not self.publisher.is_ready():
            self.publisher.start()

    def disconnect(self):
        self.publisher.terminate()
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
        self.publisher.publish(msg, Topic.of("tasks.default"))

    def start_consumer(self, handler):
        self.ensure_connected()
        receiver = self.service.create_persistent_message_receiver_builder().build(
            Queue.durable_exclusive_queue("task_queue")
        )

        class MyHandler(MessageHandler):
            def on_message(_, message):
                payload = message.get_payload_as_string()
                print("HI")

                # deserialize
                data = json.loads(payload)

                print(data)

                handler(data)

                receiver.ack(message)

        receiver.start()
        receiver.receive_async(MyHandler())
