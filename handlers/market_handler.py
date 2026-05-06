"""
Market Handler.

Responsibilities:
- React to market ticks
- Pull prices from MarketService
- Recalculate PnL snapshot
- Optionally notify UI layer (later)

No state mutation here.
"""

from events.market_events import MarketTickEvent
from services.pnl_service import PnLService


class MarketHandler:
    def __init__(self, market_service, pnl_service: PnLService, account):
        self.market_service = market_service
        self.pnl_service = pnl_service
        self.account = account

    def handle(self, event: MarketTickEvent):
        """
        On each tick:
        - get current price
        - recalculate PnL
        """

        current_price = self.market_service.get_current_price()

        report = self.pnl_service.get_report(
            self.account,
            current_price
        )

        # For now: no event emitted (can add later)
        # Example future:
        # event_bus.publish(PnLUpdatedEvent(...))

        return report