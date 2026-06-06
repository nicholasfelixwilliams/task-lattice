# Basic Usage

The following example shows the minimal setup for a Task Lattice application using Solace as the broker.

```py
import logging
from task_lattice import (
    TaskLattice,
    ConnectionDetails,
    SolaceConnectionDetails,
    TaskLatticeConfig,
    QueueConfig,
)

logging.basicConfig(level=logging.INFO)

app = TaskLattice(
    ConnectionDetails(
        broker="solace",
        config=SolaceConnectionDetails(
            host="localhost",
            port=55555,
            vpn="default",
            username="admin",
            password="admin",
        ),
    ),
    TaskLatticeConfig(
        queues=[QueueConfig(name="default")],
        default_queue="default",
    ),
)
```

## Registering Tasks

Use the `@app.task` decorator to register any sync or async function:

```py
@app.task
async def send_email(to: str, subject: str):
    print(f"Sending '{subject}' to {to}")

@app.task
def compile_report(date: str):
    print(f"Compiling report for {date}")
```

## Enqueuing Work

Create a `TaskInstance` from the decorated function, then enqueue it:

```py
task = send_email.create(kwargs={"to": "alice@example.com", "subject": "Hello"})
app.enqueue(task)
```

Enqueuing can happen from any process.

## Running a Worker

Start a worker to consume and execute tasks. This call blocks until the worker is stopped:

```py
app.start_worker()
```
