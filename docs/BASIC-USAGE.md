# Usage Documentation

The following minimal example shows how to configure a Task Lattice application with Solace as a broker.

```py
from task_lattice import TaskLattice, Depends,  SolaceConnectionDetails, TaskLatticeConfig, QueueConfig


app = TaskLattice(
    SolaceConnectionDetails(
        host="localhost", port=55555, vpn="default", username="admin", password="admin"
    ),
    TaskLatticeConfig(
        queues=[QueueConfig(name="default")],
        default_queue="default",
    ),
)

@app.task
async def some_task():
    print("Hello world!")


# Submitting a task for execution
task_instance = some_task.create()
app.enqueue(task_instance)

# Running worker process
app.start_worker()
```

In the above example we have:
 1. Defined a Task Lattice application
 2. Registered a task function for the application
 3. Submitted an instance of this task for execution
 4. Started a worker process

