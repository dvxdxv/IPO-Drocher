from dataclasses import dataclass
from datetime import datetime


@dataclass
class BaseEvent:
    timestamp: datetime