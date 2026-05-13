from .base import Broker
from .solace import SolaceBroker

BROKERS = {"solace": SolaceBroker}

__all__ = ["Broker", "BROKERS"]
