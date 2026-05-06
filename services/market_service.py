from domain.clock import SimulationClock
from domain.models import MarketData
from domain.spread_model import FixedSpreadModel


class MarketService:
    def __init__(
        self,
        market_data: MarketData,
        clock: SimulationClock,
        spread_model: FixedSpreadModel,
    ):
        self.market_data = market_data
        self.clock = clock
        self.spread_model = spread_model

    # --- core price access ---

    def get_current_index(self) -> int:
        return self.clock.current_index

    def get_current_price(self) -> float:
        idx = self.get_current_index()
        return float(self.market_data.closes[idx])

    def get_bid_ask(self):
        price = self.get_current_price()
        return self.spread_model.get_bid_ask(price)

    # --- execution logic ---

    def get_execution_price(self, side: str) -> float:
        bid, ask = self.get_bid_ask()

        if side == "BUY":
            return ask
        elif side == "SELL":
            return bid
        else:
            raise ValueError("Invalid side")

    # --- candles ---

    def get_candle(self):
        idx = self.get_current_index()

        return {
            "open": float(self.market_data.opens[idx]),
            "high": float(self.market_data.highs[idx]),
            "low": float(self.market_data.lows[idx]),
            "close": float(self.market_data.closes[idx]),
            "volume": float(self.market_data.volumes[idx]),
            "timestamp": self.market_data.timestamps[idx],
        }

    # --- batch for charts (important for performance) ---

    def get_candles_slice(self, start: int, end: int):
        return {
            "open": self.market_data.opens[start:end],
            "high": self.market_data.highs[start:end],
            "low": self.market_data.lows[start:end],
            "close": self.market_data.closes[start:end],
            "volume": self.market_data.volumes[start:end],
            "timestamp": self.market_data.timestamps[start:end],
        }