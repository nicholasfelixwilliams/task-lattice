import asyncio
from dataclasses import dataclass
import json
from solace.messaging.messaging_service import MessagingService
from solace.messaging.receiver.message_receiver import MessageHandler
from solace.messaging.resources.topic import Topic
from solace.messaging.resources.queue import Queue

@dataclass(frozen=True)
class SolaceConnectionDetails:
    host: str
    port: int 
    vpn: str
    username: str
    password: str


class SolaceBroker:

    def __init__(self, connection_details: SolaceConnectionDetails):
        self.connection_details = connection_details

        config = {
            "solace.messaging.transport.host": f"tcp://{self.connection_details.host}:{self.connection_details.port}",
            "solace.messaging.service.vpn-name": self.connection_details.vpn,
            "solace.messaging.authentication.scheme.basic.username": self.connection_details.username,
            "solace.messaging.authentication.scheme.basic.password": self.connection_details.password,
        }

        self.service = MessagingService.builder().from_properties(config).build()
        self.publisher = self.service.create_persistent_message_publisher_builder().build()

    def connect(self):
        self.service.connect()
        self.publisher.start()

    def disconnect(self):
        self.publisher.terminate()
        self.service.disconnect()

    def enqueue(self, message: dict, topic: str, priority: int):
        sol_topic = Topic.of(topic)

        msg_builder = self.service.message_builder()
        msg_builder.with_priority(priority)
        msg = msg_builder.build(json.dumps(message))

        self.publisher.publish(msg, sol_topic)

        print(f"Published {msg} to {sol_topic}")

    def listen_to_queue(self, queue: str):
        q = Queue.durable_exclusive_queue(queue)
        receiver = self.service.create_persistent_message_receiver_builder().build(q)
        loop = asyncio.get_event_loop()

        semaphore = asyncio.Semaphore(5)

        async def process_message(payload: str):
            print("⚙️ Processing async:", payload)
            await asyncio.sleep(1)

        # Proper handler class
        class MyHandler(MessageHandler):
            def on_message(self, message):
                payload = message.get_payload_as_string()
                print("📩 Received:", payload)

                async def wrapper():
                    async with semaphore:
                        await process_message(payload)
                        receiver.ack(message)

                asyncio.run_coroutine_threadsafe(wrapper(), loop)

        handler = MyHandler()

        receiver.start()
        receiver.receive_async(handler)

        loop.run_forever()
