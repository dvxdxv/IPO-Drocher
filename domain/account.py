from typing import List, NamedTuple
from domain.models import TradeEvent, TradeSide

class Position(NamedTuple):
    """Immutable snapshot of a current position."""
    quantity: int
    avg_price: float

class Account:
    def __init__(self, initial_cash: float):
        self._initial_cash: float = initial_cash
        self._cash: float = initial_cash
        self._shares: int = 0
        self._avg_price: float = 0.0
        self._realized_pnl: float = 0.0
        self._trades_log: List[TradeEvent] = []

    # --- Properties (read-only public API) ---

    @property
    def initial_cash(self) -> float:
        return self._initial_cash

    @property
    def cash(self) -> float:
        return self._cash

    @property
    def shares(self) -> int:
        return self._shares

    @property
    def avg_price(self) -> float:
        return self._avg_price

    @property
    def realized_pnl(self) -> float:
        return self._realized_pnl

    @property
    def trade_count(self) -> int:
        return len(self._trades_log)

    @property
    def trades(self) -> List[TradeEvent]:
        return self._trades_log
        
    @property
    def position(self) -> Position:
        """Returns the current position as an immutable object."""
        return Position(self._shares, self._avg_price)

    # --- Core trading logic ---

    def apply_trade(self, trade: TradeEvent) -> None:
        """
        Applies an executed trade to the account.
        This is the ONLY method that mutates account state.
        """
        if trade.quantity <= 0:
            raise ValueError("Quantity must be positive")

        if trade.side == TradeSide.BUY:
            self._apply_buy(trade)
        elif trade.side == TradeSide.SELL:
            self._apply_sell(trade)
        else:
            raise ValueError("Invalid trade side")

        self._trades_log.append(trade)

    def _apply_buy(self, trade: TradeEvent) -> None:
        cost = trade.price * trade.quantity

        if cost > self._cash:
            raise ValueError("Insufficient cash")

        new_total_shares = self._shares + trade.quantity

        if new_total_shares == 0:
            new_avg_price = 0.0
        else:
            # Standard Weighted Average Cost (WAC)
            new_avg_price = (
                (self._shares * self._avg_price) + cost
            ) / new_total_shares

        self._shares = new_total_shares
        self._avg_price = new_avg_price
        self._cash -= cost

    def _apply_sell(self, trade: TradeEvent) -> None:
        if trade.quantity > self._shares:
            raise ValueError("Insufficient shares")

        # Realized PnL calculation
        pnl = (trade.price - self._avg_price) * trade.quantity
        self._realized_pnl += pnl
        trade.pnl = pnl

        self._shares -= trade.quantity
        self._cash += trade.price * trade.quantity

        if self._shares == 0:
            self._avg_price = 0.0

    # --- Lightweight derived metrics ---

    def get_unrealized_pnl(self, current_price: float) -> float:
        if self._shares == 0:
            return 0.0
        return (current_price - self._avg_price) * self._shares

    def get_equity(self, current_price: float) -> float:
        return self._cash + (self._shares * current_price)

    def get_win_rate(self) -> float:
        sell_trades = [t for t in self._trades_log if t.side == TradeSide.SELL]

        if not sell_trades:
            return 0.0

        wins = [t for t in sell_trades if t.pnl > 0]
        return (len(wins) / len(sell_trades)) * 100