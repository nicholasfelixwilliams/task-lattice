from task_lattice.brokers.solace import SolaceBroker, SolaceConnectionDetails


if __name__ == "__main__":
    conn = SolaceConnectionDetails(
        host="localhost", port=55555, vpn="default", username="admin", password="admin"
    )

    broker = SolaceBroker(conn)
    broker.connect()

    try:
        broker.listen_to_queue("task_queue")
    finally:
        broker.disconnect()
