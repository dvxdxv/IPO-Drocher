from domain.clock import SimulationClock
from domain.models import MarketData, TradeSide
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
    
    # --- time management helpers ---
    
    def get_current_timestamp(self):
        idx = self.get_current_index()
        return self.market_data.timestamps[idx]
    
    def get_start_timestamp(self):
        return self.market_data.timestamps[0]


    def get_end_timestamp(self):
        return self.market_data.timestamps[-1]

    def get_total_steps(self) -> int:
        return len(self.market_data.closes)

    def get_elapsed_steps(self) -> int:
        return self.clock.current_index

    def get_remaining_steps(self) -> int:
        return max(0, self.get_total_steps() - 1 - self.clock.current_index)

    def get_recent_prices(self, window: int = 30):
        idx = self.get_current_index()
        start = max(0, idx - window + 1)
        return self.market_data.closes[start:idx + 1]

    # --- execution logic ---

    def get_execution_price(self, side: TradeSide) -> float:
        bid, ask = self.get_bid_ask()

        if side == TradeSide.BUY:
            return ask
        elif side == TradeSide.SELL:
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