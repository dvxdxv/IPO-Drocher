from dataclasses import dataclass
from datetime import datetime
from domain.models import TradeSide
from events.base_event import BaseEvent


@dataclass
class TradeRequestedEvent(BaseEvent):
    side: TradeSide
    quantity: int


@dataclass
class TradeValidatedEvent(BaseEvent):
    side: TradeSide
    quantity: int
    price: float


@dataclass
class TradeRejectedEvent(BaseEvent):
    reason: str


@dataclass
class TradeExecutedEvent(BaseEvent):
    side: TradeSide
    quantity: int
    price: float