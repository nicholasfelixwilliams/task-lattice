from task_lattice.broker.solace import SolaceBroker, SolaceConnectionDetails

if __name__ == "__main__":
    conn = SolaceConnectionDetails(
        host="localhost",
        port=55555,
        vpn="default",
        username="admin",
        password="admin"
    )

    broker = SolaceBroker(conn)

    broker.connect()

    for i in range(10000):
        broker.enqueue({"id": i}, "tasks/default", i%10)

    broker.disconnect()