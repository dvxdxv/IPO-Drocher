from datetime import datetime
from events.trade_events import (
    TradeRequestedEvent,
    TradeValidatedEvent,
    TradeRejectedEvent,
)


class TradeHandler:
    def __init__(self, trading_service, market_service, event_bus):
        self.trading_service = trading_service
        self.market_service = market_service
        self.event_bus = event_bus

    def handle(self, event: TradeRequestedEvent):
        price = self.market_service.get_execution_price(event.side)

        is_valid, reason = self.trading_service.validate(
            event.side, event.quantity, price
        )

        if not is_valid:
            self.event_bus.publish(
                TradeRejectedEvent(timestamp=datetime.utcnow(), reason=reason)
            )
            return

        self.event_bus.publish(
            TradeValidatedEvent(
                timestamp=datetime.utcnow(),
                side=event.side,
                quantity=event.quantity,
                price=price,
            )
        )