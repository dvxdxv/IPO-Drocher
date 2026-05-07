"""
Execution Service.

Responsible for:
- Applying validated trades to the account
- Producing execution results
- Centralizing execution logic (fees, slippage in future)

Stateless except for Account dependency.
"""

from domain.account import Account
from domain.models import TradeEvent, TradeSide


class ExecutionService:
    def __init__(self, account: Account):
        self.account = account

    def execute_trade(self, side: TradeSide, quantity: int, price: float) -> TradeEvent:
        """
        Executes a validated trade and updates account state.
        """

        trade = TradeEvent(
            side=side,
            quantity=quantity,
            price=price,
            timestamp=None
        )

        # mutate account (single source of truth)
        self.account.apply_trade(trade)

        return trade