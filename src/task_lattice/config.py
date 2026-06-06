from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class BrokerConnectionConfig:
    """Configuration for broker connection behaviour.

    Supports connection retry with backoff
    """

    max_retries: int = 5
    backoff_base: float = 1.0
    backoff_max: float = 60.0


@dataclass(frozen=True)
class TaskRetryConfig:
    """Configuration for task retry on failure."""

    max_retries: int = 3
    retry_on: tuple[type[BaseException], ...] = (Exception,)


@dataclass(frozen=True)
class SolaceConnectionDetails:
    host: str
    port: int
    vpn: str

    # TODO: Allow multiple auth schemes
    username: str
    password: str


@dataclass(frozen=True)
class ConnectionDetails:
    broker: Literal["solace", "in-memory"] = "solace"
    config: SolaceConnectionDetails | None = None
    connection: BrokerConnectionConfig = field(default_factory=BrokerConnectionConfig)


@dataclass
class QueueConfig:
    name: str
    priority_enabled: bool = False
    topic: str | None = None
    queue: str | None = None

    def __post_init__(self):
        if self.topic is None:
            self.topic = f"task-lattice/queue/in/{self.name}"
        if self.queue is None:
            self.queue = self.name


@dataclass
class TaskLatticeConfig:
    queues: list[QueueConfig]

    default_queue: str | None = None

    worker_lifecycle: Any = None
    worker_concurrency: int | None = None
    worker_shutdown_grace_period: int = 30  # in seconds

    serialization: Literal["json", "orjson", "pickle", "yaml", "toml"] = "json"

    def __post_init__(self):
        if len(self.queues) == 0:
            raise ValueError("You must define at least one queue")
        if self.default_queue is None:
            self.default_queue = self.queues[0].name
        if not any(it.name == self.default_queue for it in self.queues):
            raise ValueError("Default queue provided is not setup in queues config")
