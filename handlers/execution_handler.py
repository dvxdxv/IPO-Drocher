# handlers/execution_handler.py

import logging
from datetime import datetime, timezone

from events.trade_events import (
    TradeValidatedEvent,
    TradeExecutedEvent,
)


logger = logging.getLogger("ipo_drocher.execution_handler")


class ExecutionHandler:
    def __init__(self, execution_service, event_bus):
        self.execution_service = execution_service
        self.event_bus = event_bus

    def handle(self, event: TradeValidatedEvent):
        """
        Execute validated trade.
        """

        logger.info(
            "EXECUTION_START | side=%s | qty=%s | price=%s",
            event.side,
            event.quantity,
            event.price,
        )

        trade = self.execution_service.execute_trade(
            side=event.side,
            quantity=event.quantity,
            price=event.price,
            timestamp=event.timestamp,
        )

        logger.info(
            "EXECUTION_DONE | side=%s | qty=%s | price=%s",
            trade.side,
            trade.quantity,
            trade.price,
        )

        logger.info(
            "ACCOUNT_STATE | cash=%s | shares=%s | avg_price=%s",
            self.execution_service.account.cash,
            self.execution_service.account.shares,
            self.execution_service.account.avg_price,
        )

        self.event_bus.publish(
            TradeExecutedEvent(
                timestamp=datetime.now(timezone.utc),
                side=trade.side,
                quantity=trade.quantity,
                price=trade.price,
            ),
            publisher="ExecutionHandler",
            metadata={
                "action": "trade_executed",
                "side": trade.side.value,
                "quantity": trade.quantity,
                "price": trade.price,
            },
        )

        return trade