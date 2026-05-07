import numpy as np
from datetime import datetime, timezone

from domain.account import Account
from domain.clock import SimulationClock
from domain.models import MarketData, TradeSide

from domain.spread_model import FixedSpreadModel

from services.market_service import MarketService
from services.trading_service import TradingService
from services.execution_service import ExecutionService
from services.pnl_service import PnLService
from services.session_service import SessionService

from events.event_bus import EventBus
from events.trade_events import TradeRequestedEvent

from handlers.trade_handler import TradeHandler
from handlers.execution_handler import ExecutionHandler


def create_mock_data():
    return MarketData(
        closes=np.array([10.0, 12.0, 15.0]),
        opens=np.array([10.0, 12.0, 15.0]),
        highs=np.array([10.0, 12.0, 15.0]),
        lows=np.array([10.0, 12.0, 15.0]),
        volumes=np.array([100, 100, 100]),
        timestamps=np.array(["t1", "t2", "t3"]),
    )


def test_full_trading_flow():
    # --- setup core ---
    data = create_mock_data()
    clock = SimulationClock(max_index=3)
    spread = FixedSpreadModel()

    account = Account(1000)

    market_service = MarketService(data, clock, spread)
    trading_service = TradingService(account)
    execution_service = ExecutionService(account)
    pnl_service = PnLService()
    session_service = SessionService(pnl_service)

    # --- event system ---
    bus = EventBus()

    trade_handler = TradeHandler(trading_service, market_service, bus)
    execution_handler = ExecutionHandler(execution_service, bus)

    bus.subscribe(TradeRequestedEvent, trade_handler.handle)
    from events.trade_events import TradeValidatedEvent
    bus.subscribe(TradeValidatedEvent, execution_handler.handle)

    # --- BUY at t=0 ---
    bus.publish(
        TradeRequestedEvent(
            timestamp=datetime.now(timezone.utc),
            side=TradeSide.BUY,
            quantity=10,
        )
    )

    assert account.shares == 10

    # --- move time ---
    clock.tick()  # price goes to 12

    # --- SELL at t=1 ---
    bus.publish(
        TradeRequestedEvent(
            timestamp=datetime.now(timezone.utc),
            side=TradeSide.SELL,
            quantity=10,
        )
    )

    assert account.shares == 0
    assert account.realized_pnl > 0

    # --- final result ---
    final_price = market_service.get_current_price()
    result = session_service.get_session_result(account, final_price)

    assert result["final_equity"] > 1000
    assert result["grade"] in ["A+", "A", "B", "C", "D", "F"]