"""
Session Handler.

Responsibilities:
- Handle session lifecycle
- Detect end of data
- Produce final session result
"""

from datetime import datetime
from events.market_events import MarketClosedEvent


class SessionHandler:
    def __init__(self, session_service, market_service, account):
        self.session_service = session_service
        self.market_service = market_service
        self.account = account

    def handle(self, event: MarketClosedEvent):
        """
        Called when simulation ends.
        """

        final_price = self.market_service.get_current_price()

        result = self.session_service.get_session_result(
            self.account,
            final_price
        )

        # Future:
        # save to DB
        # publish SessionFinishedEvent

        return result