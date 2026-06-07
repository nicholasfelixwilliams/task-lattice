import pytest

from task_lattice import TaskLattice, TaskRetryConfig


def test_sync_task(app: TaskLattice):
    @app.task
    def function(): ...

    assert len(app._task_registry) == 1

    task = next(iter(app._task_registry.values()))

    assert not task.is_async
    assert task.name == "function"
    assert task.lifecycle is None


def test_async_task(app: TaskLattice):
    @app.task
    async def function(): ...

    assert len(app._task_registry) == 1

    task = next(iter(app._task_registry.values()))

    assert task.is_async
    assert task.name == "function"
    assert task.lifecycle is None


def test_sync_task_with_options(app: TaskLattice):
    @app.task(name="something.unique")
    def function(): ...

    assert len(app._task_registry) == 1

    task = next(iter(app._task_registry.values()))

    assert not task.is_async
    assert task.name == "something.unique"
    assert task.lifecycle is None


def test_async_task_with_options(app: TaskLattice):
    @app.task(name="something.unique")
    async def function(): ...

    assert len(app._task_registry) == 1

    task = next(iter(app._task_registry.values()))

    assert task.is_async
    assert task.name == "something.unique"
    assert task.lifecycle is None


def test_duplicate_task_name_raises(app: TaskLattice):
    @app.task(name="duplicate")
    def first(): ...

    with pytest.raises(ValueError, match="already registered"):

        @app.task(name="duplicate")
        def second(): ...


def test_retry_config_stored(app: TaskLattice):
    retry = TaskRetryConfig(max_retries=3, retry_on=(ValueError,))

    @app.task(retry=retry)
    def my_task(): ...

    task = app._task_registry["my_task"]
    assert task.retry is retry
