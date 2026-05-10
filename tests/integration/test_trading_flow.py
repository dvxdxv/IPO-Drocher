import pytest
from datetime import datetime, timezone

from adapters.file_storage_adapter import FileStorageAdapter
from adapters.data_loader import CsvDataLoader

from domain.account import Account
from domain.clock import SimulationClock
from domain.spread_model import FixedSpreadModel
from domain.models import TradeSide

from services.market_service import MarketService
from services.trading_service import TradingService
from services.execution_service import ExecutionService
from services.pnl_service import PnLService
from services.session_service import SessionService

from events.event_bus import EventBus
from events.trade_events import TradeRequestedEvent, TradeValidatedEvent
from events.market_events import MarketTickEvent, MarketClosedEvent

from handlers.trade_handler import TradeHandler
from handlers.execution_handler import ExecutionHandler
from handlers.market_handler import MarketHandler
from handlers.session_handler import SessionHandler


@pytest.fixture
def engine():
    # --- load real CSV ---
    storage = FileStorageAdapter("data/")
    files = storage.list_csv_files()
    assert files, "No CSV files found"

    loader = CsvDataLoader()
    market_data = loader.load(storage.get_file_path(files[0]))

    # --- core ---
    account = Account(initial_cash=10_000)
    clock = SimulationClock(max_index=len(market_data.closes))
    spread = FixedSpreadModel()

    # --- services ---
    market = MarketService(market_data, clock, spread)
    trading = TradingService(account)
    execution = ExecutionService(account)
    pnl = PnLService()
    session = SessionService(pnl)

    # --- event bus ---
    bus = EventBus()

    trade_handler = TradeHandler(trading, market, bus)
    execution_handler = ExecutionHandler(execution, bus)
    market_handler = MarketHandler(market, pnl, account)
    session_handler = SessionHandler(session, market, account)

    bus.subscribe(TradeRequestedEvent, trade_handler.handle)
    bus.subscribe(TradeValidatedEvent, execution_handler.handle)
    bus.subscribe(MarketTickEvent, market_handler.handle)
    bus.subscribe(MarketClosedEvent, session_handler.handle)

    return {
        "account": account,
        "clock": clock,
        "market": market,
        "bus": bus,
    }


def test_full_trading_flow(engine):
    account = engine["account"]
    clock = engine["clock"]
    market = engine["market"]
    bus = engine["bus"]

    # --- 1. first tick ---
    assert clock.tick()

    bus.publish(
        MarketTickEvent(
            timestamp=datetime.now(timezone.utc),
            index=clock.current_index
        )
    )

    price_buy = market.get_current_price()

    # --- 2. BUY ---
    bus.publish(
        TradeRequestedEvent(
            timestamp=datetime.now(timezone.utc),
            side=TradeSide.BUY,
            quantity=10
        )
    )

    assert account.shares == 10
    assert account.cash < 10_000

    # --- 3. move forward in time ---
    for _ in range(5):
        assert clock.tick()
        bus.publish(
            MarketTickEvent(
                timestamp=datetime.now(timezone.utc),
                index=clock.current_index
            )
        )

    price_sell = market.get_current_price()

    # --- 4. SELL ---
    bus.publish(
        TradeRequestedEvent(
            timestamp=datetime.now(timezone.utc),
            side=TradeSide.SELL,
            quantity=10
        )
    )

    assert account.shares == 0

    # --- 5. finish session ---
    result = bus.publish(
        MarketClosedEvent(timestamp=datetime.now(timezone.utc))
    )

    # --- 6. assertions ---
    assert "final_equity" in result
    assert "total_pnl" in result
    assert "grade" in result

    # sanity check
    assert result["final_equity"] > 0

    # pnl direction check (optional)
    expected_pnl = (price_sell - price_buy) * 10
    assert abs(result["total_pnl"] - expected_pnl) < 1e-6