# Dependency Injection

Task Lattice includes a lightweight dependency injection system inspired by FastAPI.

Dependencies are declared as default parameter values using `Depends` and are resolved automatically at task execution time.

## Basic Usage

```py
from task_lattice import Depends

def get_context():
    return {"user": "alice"}

@app.task
def my_task(context=Depends(get_context)):
    print(context)
```

When the task executes:
1. `get_context()` is called.
2. The return value is injected as the `context` argument.
3. The task receives the resolved value.

Dependencies can be synchronous, asynchronous, context managers or asynchronous context managers.

## Context Manager Dependencies

Context managers are the right tool when a dependency needs cleanup after the task finishes (database sessions, file handles, HTTP clients, etc.).


```py
from contextlib import contextmanager

@contextmanager
def get_db():
    db = open_db_connection()
    try:
        yield db
    finally:
        db.close()

@app.task
def write_record(data: dict, db=Depends(get_db)):
    db.insert(data)
```

The context manager is entered before the task runs and exited (including the `finally` block) after the task completes — even if the task raises an exception.

## Multiple Dependencies

A task can declare as many `Depends` parameters as needed:

```python
@app.task
async def process(
    db=Depends(get_db),
    cache=Depends(get_cache),
    config=Depends(get_config),
):
    ...
```
