from adapters.file_storage_adapter import FileStorageAdapter
from adapters.data_loader import CsvDataLoader

from domain.account import Account
from domain.clock import SimulationClock
from domain.spread_model import FixedSpreadModel

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


def create_engine(deposit: float, asset_file: str):
    # --- data ---
    loader = CsvDataLoader()
    market_data = loader.load(asset_file)

    # --- domain ---
    account = Account(initial_cash=deposit)
    clock = SimulationClock(max_index=len(market_data.closes))
    spread = FixedSpreadModel()

    # --- services ---
    market = MarketService(market_data, clock, spread)
    trading = TradingService(account)
    execution = ExecutionService(account)
    pnl = PnLService()
    session = SessionService(pnl)

    # --- bus ---
    bus = EventBus()

    # --- handlers ---
    trade_handler = TradeHandler(trading, market, bus)
    execution_handler = ExecutionHandler(execution, bus)
    market_handler = MarketHandler(market, pnl, account)
    session_handler = SessionHandler(session, market, account)

    # --- wiring ---
    bus.subscribe(TradeRequestedEvent, trade_handler.handle)
    bus.subscribe(TradeValidatedEvent, execution_handler.handle)
    bus.subscribe(MarketTickEvent, market_handler.handle)
    bus.subscribe(MarketClosedEvent, session_handler.handle)

    return {
        "bus": bus,
        "account": account,
        "clock": clock,
        "market": market,
    }