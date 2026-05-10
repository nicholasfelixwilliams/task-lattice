# Dependency Injection

Task Lattice includes a lightweight dependency injection system inspired by FastAPI.

Dependencies are resolved automatically at task execution time using the `Depends` class.

All dependencies are scoped to a single task execution.


## Basic Usage

Dependencies are declared as default values on task parameters.

```py
from task_lattice import Depends


def get_context():
    return {"user": "alice"}


@app.task
def my_task(context=Depends(get_context)):
    print(context)
```

When the task executes:
1. get_context() is called
2. The returned value is injected into the task
3. The task receives the resolved dependency

Dependencies can be synchronous, asynchronous, context managers or asynchronous context managers.

## Context Managers

Context managers can be useful for:
 - Database sessions
 - Profilers
 - Temporary resources
 - Tracing

```py
from contextlib import contextmanager


@contextmanager
def get_db():
    print("Opening DB connection")

    yield {"db": "connection"}

    print("Closing DB connection")

@app.task
def my_task(db=Depends(get_db)):
    print(db)
```

The context manager is automatically entered and cleaned up for each task execution.