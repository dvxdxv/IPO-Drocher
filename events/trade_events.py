from dataclasses import dataclass
from datetime import datetime
from events.base_event import BaseEvent


@dataclass
class TradeRequestedEvent(BaseEvent):
    side: str
    quantity: int


@dataclass
class TradeValidatedEvent(BaseEvent):
    side: str
    quantity: int
    price: float


@dataclass
class TradeRejectedEvent(BaseEvent):
    reason: str


@dataclass
class TradeExecutedEvent(BaseEvent):
    side: str
    quantity: int
    price: float