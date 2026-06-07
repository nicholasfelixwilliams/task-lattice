import pytest

from task_lattice import QueueConfig, TaskLatticeConfig


class TestQueueConfig:
    def test_auto_generates_topic_and_queue(self):
        q = QueueConfig(name="default")
        assert q.topic == "task-lattice/queue/in/default"
        assert q.queue == "default"

    def test_custom_topic_and_queue_preserved(self):
        q = QueueConfig(name="default", topic="my/topic", queue="my-queue")
        assert q.topic == "my/topic"
        assert q.queue == "my-queue"


class TestTaskLatticeConfig:
    def test_defaults_to_first_queue(self):
        config = TaskLatticeConfig(queues=[QueueConfig(name="alpha")])
        assert config.default_queue == "alpha"

    def test_explicit_default_queue(self):
        config = TaskLatticeConfig(
            queues=[QueueConfig(name="a"), QueueConfig(name="b")],
            default_queue="b",
        )
        assert config.default_queue == "b"

    def test_empty_queues_raises(self):
        with pytest.raises(ValueError):
            TaskLatticeConfig(queues=[])

    def test_unknown_default_queue_raises(self):
        with pytest.raises(ValueError):
            TaskLatticeConfig(queues=[QueueConfig(name="q")], default_queue="missing")
