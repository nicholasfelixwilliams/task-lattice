import pytest

from task_lattice import TaskLattice


def test_enqueue_uses_default_queue(app: TaskLattice):
    @app.task
    def my_task(): ...

    instance = my_task.create()
    app.enqueue(instance)
    assert instance.queue == "default"


def test_enqueue_async(app: TaskLattice):
    @app.task
    async def my_task(): ...

    instance = my_task.create()
    app.enqueue(instance)


def test_enqueue_explicit_queue(multi_queue_app: TaskLattice):
    @multi_queue_app.task
    def my_task(): ...

    instance = my_task.create()
    multi_queue_app.enqueue(instance, queue="priority")
    assert instance.queue == "priority"


def test_enqueue_unknown_queue_raises(app: TaskLattice):
    @app.task
    def my_task(): ...

    instance = my_task.create()
    with pytest.raises(ValueError, match="not configured"):
        app.enqueue(instance, queue="nonexistent")
