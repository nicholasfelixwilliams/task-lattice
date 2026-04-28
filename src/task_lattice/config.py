from dataclasses import dataclass


@dataclass(frozen=True)
class SolaceConnectionDetails:
    host: str
    port: int
    vpn: str

    # TODO: Allow multiple auth schemes
    username: str
    password: str


@dataclass(frozen=True)
class QueueConfig:
    name: str
    topic: str


@dataclass(frozen=True)
class TaskLatticeConfig:
    queues: list[QueueConfig]

    default_queue: str
