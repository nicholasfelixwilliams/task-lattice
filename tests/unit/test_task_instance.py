from task_lattice import TaskLattice, TaskRetryConfig
from task_lattice.task import TaskInstance


def test_create_returns_task_instance(app: TaskLattice):
    @app.task
    def my_task(): ...

    instance = my_task.create()
    assert isinstance(instance, TaskInstance)
    assert instance.task_name == "my_task"


def test_create_with_args_and_kwargs(app: TaskLattice):
    @app.task
    def my_task(): ...

    instance = my_task.create(args=[1, 2], kwargs={"x": 3})
    assert instance.args == [1, 2]
    assert instance.kwargs == {"x": 3}


def test_create_with_priority(app: TaskLattice):
    @app.task
    def my_task(): ...

    instance = my_task.create(priority=1)
    assert instance.priority == 1


def test_instance_retry_overrides_definition_retry(app: TaskLattice):
    @app.task(retry=TaskRetryConfig(max_retries=1))
    def my_task(): ...

    override = TaskRetryConfig(max_retries=5)
    instance = my_task.create(retry=override)
    assert instance.max_retries == 5


def test_loading_from_message(app: TaskLattice):
    class CustomException(Exception): ...

    @app.task(
        retry=TaskRetryConfig(
            retry_on=(
                ValueError,
                CustomException,
            )
        )
    )
    def my_task(): ...

    original = my_task.create()
    new = TaskInstance.from_message(original.message)

    assert new.task_name == original.task_name
    assert new.args == original.args
    assert new.kwargs == original.kwargs
    assert new.priority == original.priority
    assert new.attempt == original.attempt
    assert new.max_retries == original.max_retries
    assert new.queue == original.queue
    assert new.creation_timestamp == original.creation_timestamp
