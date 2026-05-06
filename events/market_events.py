"""
Market-related events.

These events are produced by the clock / market layer
and consumed by handlers.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketTickEvent:
    """
    Fired on every clock tick (new market data index).
    """
    timestamp: datetime
    index: int


@dataclass
class MarketClosedEvent:
    """
    Fired when market data is exhausted.
    """
    timestamp: datetime