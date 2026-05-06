from enum import Enum
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class MarketData:
    closes: np.ndarray
    opens: np.ndarray
    highs: np.ndarray
    lows: np.ndarray
    volumes: np.ndarray
    timestamps: np.ndarray


@dataclass
class TradeEvent:
    side: str  # "BUY" or "SELL"
    price: float
    quantity: int
    timestamp: Optional[str] = None


@dataclass
class Position:
    quantity: int = 0
    avg_price: float = 0.0
    
class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
