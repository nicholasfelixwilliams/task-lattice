def test_sync_task(app):
    @app.task
    def function(): ...

    assert len(app._task_registry) == 1

    task = next(iter(app._task_registry.values()))

    assert not task.is_async
    assert task.name == "function"
    assert task.lifeycle is None


def test_async_task(app):
    @app.task
    async def function(): ...

    assert len(app._task_registry) == 1

    task = next(iter(app._task_registry.values()))

    assert task.is_async
    assert task.name == "function"
    assert task.lifeycle is None


def test_sync_task_with_options(app):
    @app.task(name="something.unique")
    def function(): ...

    assert len(app._task_registry) == 1

    task = next(iter(app._task_registry.values()))

    assert not task.is_async
    assert task.name == "something.unique"
    assert task.lifeycle is None


def test_async_task_with_options(app):
    @app.task(name="something.unique")
    async def function(): ...

    assert len(app._task_registry) == 1

    task = next(iter(app._task_registry.values()))

    assert task.is_async
    assert task.name == "something.unique"
    assert task.lifeycle is None
