from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SolaceConnectionDetails:
    host: str
    port: int
    vpn: str

    # TODO: Allow multiple auth schemes
    username: str
    password: str


@dataclass
class QueueConfig:
    name: str
    priority_enabled: bool = False
    topic: str | None = None

    def __post_init__(self):
        if self.topic is None:
            self.topic = f"task-lattice/queue/in/{self.name}"


@dataclass
class TaskLatticeConfig:
    queues: list[QueueConfig]

    default_queue: str | None = None

    serialization: Literal["json", "orjson", "pickle", "yaml", "toml"] = "json"

    def __post_init__(self):
        if len(self.queues) == 0:
            raise ValueError("You must define at least one queue")
        if self.default_queue is None:
            self.default_queue = self.queues[0].name
        if not any(it.name == self.default_queue for it in self.queues):
            raise ValueError("Default queue provided is not setup in queues config")
