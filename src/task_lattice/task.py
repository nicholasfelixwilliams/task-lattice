import builtins
import importlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncContextManager, Callable, ContextManager

from .config import TaskLatticeConfig, TaskRetryConfig


def _exc_types_to_names(exc_types: tuple[type[BaseException], ...]) -> list[str]:
    """Serialise a tuple of exception types to a list of qualified name strings."""
    return [f"{t.__module__}.{t.__qualname__}" for t in exc_types]


def _names_to_exc_types(names: list[str]) -> tuple[type[BaseException], ...]:
    """Deserialise qualified name strings back to exception types.

    Unresolvable names are silently skipped.  If no names resolve, falls back
    to ``(Exception,)`` so the retry check never crashes the worker.
    """
    result: list[type[BaseException]] = []
    for name in names:
        module_name, _, cls_name = name.rpartition(".")
        try:
            if not module_name or module_name == "builtins":
                exc_type = getattr(builtins, cls_name, None)
            else:
                module = importlib.import_module(module_name)
                exc_type = getattr(module, cls_name, None)
        except ImportError:
            exc_type = None

        if (
            exc_type is not None
            and isinstance(exc_type, type)
            and issubclass(exc_type, BaseException)
        ):
            result.append(exc_type)

    return tuple(result) if result else (Exception,)


@dataclass
class TaskDefinition:
    """Metadata for a registered task"""

    name: str
    func: Callable
    is_async: bool
    lifecycle: AsyncContextManager | ContextManager | None = None
    retry: TaskRetryConfig | None = None


class TaskInstance:
    """A single invocation of a task"""

    def __init__(
        self,
        task_name: str,
        args: list,
        kwargs: dict,
        priority: int = 2,
        attempt: int = 0,
        max_retries: int = 0,
        retry_on: tuple[type[BaseException], ...] = (Exception,),
        queue: str | None = None,
        creation_timestamp: str | None = None,
    ):
        self.task_name = task_name
        self.args = args
        self.kwargs = kwargs
        self.priority = priority
        self.attempt = attempt
        self.max_retries = max_retries
        self.retry_on = retry_on
        self.queue = queue
        self.creation_timestamp = (
            creation_timestamp or datetime.now(tz=timezone.utc).isoformat()
        )

    @classmethod
    def from_message(cls, message: dict) -> "TaskInstance":
        return cls(
            task_name=message["task_name"],
            args=message.get("args", []),
            kwargs=message.get("kwargs", {}),
            priority=message.get("priority", 2),
            attempt=message.get("attempt", 0),
            max_retries=message.get("max_retries", 0),
            retry_on=_names_to_exc_types(
                message.get("retry_on", ["builtins.Exception"])
            ),
            queue=message.get("queue"),
            creation_timestamp=message.get("creation_timestamp"),
        )

    @property
    def message(self) -> dict:
        return {
            "task_name": self.task_name,
            "args": self.args,
            "kwargs": self.kwargs,
            "priority": self.priority,
            "attempt": self.attempt,
            "max_retries": self.max_retries,
            "retry_on": _exc_types_to_names(self.retry_on),
            "queue": self.queue,
            "creation_timestamp": self.creation_timestamp,
            "enqueue_timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }


class TaskFunction:
    """Wrapper returned by the ``@app.task`` decorator"""

    def __init__(
        self, func: Callable, task_def: TaskDefinition, config: TaskLatticeConfig
    ):
        self.func = func
        self.task_def = task_def
        self.config = config

    def create(
        self,
        args: list | None = None,
        kwargs: dict | None = None,
        priority: int = 2,
        retry: TaskRetryConfig | None = None,
    ) -> TaskInstance:
        # Instance-level config takes precedence over definition-level
        effective_retry = retry or self.task_def.retry

        return TaskInstance(
            task_name=self.task_def.name,
            args=args or [],
            kwargs=kwargs or {},
            priority=priority,
            attempt=0,
            max_retries=effective_retry.max_retries if effective_retry else 0,
            retry_on=effective_retry.retry_on if effective_retry else (Exception,),
        )

    def __call__(self, *args, **kwargs):
        raise TypeError(
            f"Task '{self.task_def.name}' cannot be called directly. "
            "Use .create() to build a TaskInstance and enqueue it via app.enqueue()."
        )
