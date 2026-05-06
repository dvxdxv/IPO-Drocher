from datetime import datetime
from events.trade_events import TradeValidatedEvent, TradeExecutedEvent


class ExecutionHandler:
    def __init__(self, execution_service, event_bus):
        self.execution_service = execution_service
        self.event_bus = event_bus

    def handle(self, event: TradeValidatedEvent):
        trade = self.execution_service.execute_trade(
            side=event.side,
            quantity=event.quantity,
            price=event.price,
        )

        self.event_bus.publish(
            TradeExecutedEvent(
                timestamp=datetime.utcnow(),
                side=trade.side,
                quantity=trade.quantity,
                price=trade.price,
            )
        )