from task_lattice.broker import SolaceBroker, SolaceConnectionDetails, TaskInstance
from task_lattice.task import Task

from solace.messaging.messaging_service import MessagingService

MessagingService.set_core_messaging_log_level("INFO")

if __name__ == "__main__":
    conn = SolaceConnectionDetails(
        host="localhost", port=55555, vpn="default", username="admin", password="admin"
    )

    broker = SolaceBroker(conn)

    broker.connect()

    for i in range(3):
        broker.publish(
            TaskInstance(
                task=Task("test", None, False), config=None, args=[], kwargs={}
            )
        )

    broker.disconnect()
