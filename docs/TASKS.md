# Tasks

Tasks are Python functions registered with a `TaskLattice` application.

Tasks can be:
- Synchronous
- Asynchronous
- Parameterised
- Enqueued for background execution
- Executed by workers


## Defining a Task

Tasks are registered using the `@app.task` decorator.

```py
@app.task
async def send_email():
    print("Sending email")

@app.task
def compile_report(date: str):
    print("Compiling report")
```

Both sync and async tasks are supported automatically. Tasks can support args and kwargs provided they can be serialised using the serialisation type you have chosen (default json).

## Naming tasks

Tasks are given a default name, but this can be explicitly set using a custom name:

```py
@app.task(name="tasks.email")
async def send_email():
    print("Sending email")
```

**Note** - Names must be unique.

## Task Lifecycle

Tasks can be given a lifecycle context manager. This will be applied upon execution by the worker.

```py
@contextmanager
def profiling():
    print("Starting profiling")

    yield

    print("Stopping profiling")

@app.task(lifecycle=profiling)
async def send_email():
    print("Sending email")
```

We support both sync and async context managers.

## Creating a Task Instance

When you define a task in code you create a "Task Function" (by using the decorator). This automatically registers a "Task Definition" in your application. To send a task to a worker you need to create a "Task Instance". 

```py
task_instance = send_email.create()
```

Once you have the Task Instanc you can send it to the broker to be executed by a worker:

```py
app.enqueue(task_instance)
```

When creating a task instance you have various options available to you:


```py
# Customise queue
task_instance = send_email.create(queue="emails")

# Customise arguments
task_instance = send_email.create(args=[1,2,3], kwargs={"a": 1})
```
