# Workers

Workers are long-running processes that consume task messages from one or more queues and execute them concurrently.

A worker:
- Connects to the configured broker (with automatic retry)
- Listens for incoming task messages
- Executes tasks concurrently up to the configured limit
- Handles graceful shutdown on SIGINT / SIGTERM
- Supports sync and async tasks natively
- Supports worker and task lifecycle hooks

## Starting a Worker

```py
from your_app import app

app.start_worker()
```

This blocks until the worker is stopped. By default it listens on all configured queues.

## Targeting Specific Queues

```py
app.start_worker(queues=["emails", "reports"])
```

## Concurrency

You can configure the maximum concurrency of a worker either in the Task Lattice application (as a default) or for the worker itself. This defines how many tasks the worker can execute at the same time. 

**Note** - For some brokers (incl. Solace) you may also want to configure the broker to limit the number of messages pushed to each consumer. 

```py
app = TaskLattice(
    connection_details=...,
    config=TaskLatticeConfig(
        worker_concurrency=50,
        ...
    ),
)

# Or per-worker (overrides the config value)
app.start_worker(concurrency=20)
```

## Shutdown

Workers respond to:
- **SIGINT** (`Ctrl+C` in a terminal)
- **SIGTERM** (sent by Kubernetes, Docker, systemd, etc.)

On receiving a shutdown signal the worker will:

1. Stop accepting new messages from the broker.
2. Wait for all in-flight tasks to complete.
3. Run worker lifecycle cleanup (database pool teardown, etc.).
4. Exit.

By default the worker waits up to **30 seconds** for in-flight tasks. Tasks that exceed the grace period are abandoned with a warning.

```py
TaskLatticeConfig(
    worker_shutdown_grace_period=60,  # seconds
    ...
)
```

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
    pool = await create_db_pool()
    print("Worker starting — pool ready")

    yield

    await pool.close()
    print("Worker stopping — pool closed")

app = TaskLattice(
    connection_details=...,
    config=TaskLatticeConfig(
        worker_lifecycle=lifecycle(),
        ...
    ),
)
```

Both sync (`contextmanager`) and async (`asynccontextmanager`) context managers are supported.

## Task Execution Flow

When a task message is received the following happens in order:

1. The message is deserialised and the task looked up in the registry.
2. The task is scheduled on the worker event loop.
3. The concurrency semaphore is acquired (blocks if at the limit).
4. Dependencies are resolved via `Depends`.
5. The task lifecycle context manager (if any) is entered.
6. The task function is executed (sync tasks run in a thread pool).
7. The task lifecycle is cleaned up.
8. The semaphore is released.
9. Execution time is logged.

If the task raises an exception, it is logged (with a full traceback) and the worker continues processing subsequent messages.

## Logging

Workers emit structured log messages under the `task-lattice` logger.
