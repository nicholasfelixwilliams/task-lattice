import pytest

from task_lattice import (
    TaskLattice,
    ConnectionDetails,
    TaskLatticeConfig,
    QueueConfig,
)


@pytest.fixture
def app():
    return TaskLattice(
        ConnectionDetails(broker="in-memory"),
        TaskLatticeConfig(
            queues=[QueueConfig(name="default")],
            default_queue="default",
        ),
    )
