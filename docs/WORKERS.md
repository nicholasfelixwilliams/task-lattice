# Workers

Workers are long-running processes responsible for consuming and executing tasks from configured queues.

A worker:
- Connects to the configured broker
- Listens for incoming task messages
- Executes tasks concurrently
- Handles graceful shutdown
- Supports sync and async tasks
- Supports task and worker lifecycle hooks

## Starting a Worker

Workers are started from a `TaskLattice` application instance.

```py
from .your_app import app

app.start_worker()
```

By default this will listen to all configured queues.

## Listening to Specific Queues

You can target only specific queues by referencing their name (as configured in your Task Lattice app):

```py
app.start_worker(queues=["emails", "report"])
```

## Concurrency

You can configure the maximum concurrency of a worker either in the Task Lattice application (as a default) or for the worker itself. This defines how many tasks the worker can execute at the same time. 

**Note** - For some brokers (incl. Solace) you may also want to configure the broker to limit the number of messages pushed to each consumer. 

```py
app = TaskLattice(
    connection_details=...,
    config=TaskLatticeConfig(
        worker_concurrency=100,
        ...
    ),
)

app.start_worker(concurrency=100)
```

If no value is provided, this will default to 100.

## Shutdown

Workers support graceful shutdown using:
 - SIGINT (Ctrl+C)
 - SIGTERM (Kubernetes / container shutdown)

During shutdown the worker will:
 - Stop consuming new messages
 - Wait for running tasks to complete
 - Shut down cleanly

By default workers wait up to 30 seconds for running tasks to finish. This can be configured using the "worker_shutdown_grace_period" config.

## Worker Lifecycle

Worker lifecycles allow setup and cleanup logic to run for the lifetime of the worker process.

This is useful for:
 - External connection pools (Database, Redis, ...)
 - Telemetry exporters
 - Shared application resources

Worker lifecycles can be sync or async context managers.

```py
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifecycle():
    print("Worker starting")

    yield

    print("Worker shutting down")

app = TaskLattice(
    connection_details=...,
    config=TaskLatticeConfig(
        worker_lifecycle=lifecycle,
        ...
    ),
)
```

## Task Execution Flow

The following steps occur when a task is executed:
1. A worker receives a task message from the broker
2. The task is scheduled on the worker event loop
3. Concurrency limits are applied
4. Dependencies are resolved
5. Task lifecycle hooks are entered
6. The task is executed
7. Lifecycle hooks are cleaned up
8. Task completion is logged

## Worker Logging

Workers automatically log:
- Worker startup
- Queue subscriptions
- Task execution timing
- Shutdown events
- Unknown task warnings