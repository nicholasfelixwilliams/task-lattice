import pytest

from task_lattice import (
    TaskLattice,
    ConnectionDetails,
    TaskLatticeConfig,
    QueueConfig,
)


@pytest.fixture
def app() -> TaskLattice:
    return TaskLattice(
        ConnectionDetails(broker="in-memory"),
        TaskLatticeConfig(
            queues=[QueueConfig(name="default")],
            default_queue="default",
        ),
    )


@pytest.fixture
def multi_queue_app() -> TaskLattice:
    return TaskLattice(
        ConnectionDetails(broker="in-memory"),
        TaskLatticeConfig(
            queues=[QueueConfig(name="default"), QueueConfig(name="priority")],
            default_queue="default",
        ),
    )
