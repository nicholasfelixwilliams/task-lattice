# Tasks

Tasks are Python functions registered with a `TaskLattice` application.

Tasks can be:
- Synchronous
- Asynchronous
- Parameterised
- Enqueued for background execution
- Executed by workers


## Defining a Task

Use the `@app.task` decorator on any sync or async function:

```py
@app.task
async def send_email(to: str, subject: str):
    print(f"Sending '{subject}' to {to}")

@app.task
def compile_report(date: str):
    print(f"Compiling report for {date}")
```

Both sync and async tasks are supported automatically. Tasks can support args and kwargs provided they can be serialised using the serialisation type you have chosen (default json).

## Custom Task Names

Tasks are named after their function by default. You can override this:

```py
@app.task(name="email.send")
async def send_email(to: str):
    ...
```

Task names must be unique across the application.

## Task Lifecycle

A lifecycle context manager can be attached to a task. It is entered every time that task is executed by a worker — useful for profiling, tracing, or per-execution resource management.

```py
from contextlib import contextmanager

@contextmanager
def profiling():
    print("Profiling start")
    yield
    print("Profiling end")

@app.task(lifecycle=profiling())
async def send_email(to: str):
    ...
```

Both sync (`contextmanager`) and async (`asynccontextmanager`) context managers are supported.

## Automatic Retry

Tasks can be configured to retry automatically on failure using `TaskRetryConfig`.

By default, Task Lattice retries on any `Exception`. Use `retry_on` to limit
retries to specific exception types.

This config can be set at definition level and instance level.

## Creating a Task Instance

Calling `@app.task` wraps the function in a `TaskFunction` and registers it
with the application. To dispatch it for execution you must create a
`TaskInstance`:

```py
task_instance = send_email.create(kwargs={"to": "alice@example.com"})
```

Then enqueue it:

```py
app.enqueue(task_instance)
```

When creating a task instance you have various options available to you:


```py
# Customise queue
task_instance = send_email.create(queue="emails")

# Customise arguments
task_instance = send_email.create(args=[1,2,3], kwargs={"a": 1})

# Customise priority
task_instance = send_email.create(kwargs={"to": "ceo@example.com"}, priority=1)
```
