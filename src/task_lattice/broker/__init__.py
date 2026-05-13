from .base import Broker
from .in_memory import InMemoryBroker
from .solace import SolaceBroker

BROKERS = {"in-memory": InMemoryBroker, "solace": SolaceBroker}

__all__ = ["Broker", "BROKERS"]
