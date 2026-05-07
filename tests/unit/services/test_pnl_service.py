from domain.account import Account
from domain.models import TradeEvent, TradeSide
from services.pnl_service import PnLService


def test_unrealized_pnl():
    acc = Account(1000)
    pnl = PnLService()

    acc.apply_trade(TradeEvent(side=TradeSide.BUY, price=10, quantity=10))  # avg = 10

    result = pnl.calculate_unrealized(acc, current_price=15)

    assert result == 50  # (15-10)*10


def test_realized_pnl():
    acc = Account(1000)
    pnl = PnLService()

    acc.apply_trade(TradeEvent(side=TradeSide.BUY, price=10, quantity=10))
    acc.apply_trade(TradeEvent(side=TradeSide.SELL, price=20, quantity=5))  # profit = 50

    result = pnl.calculate_realized(acc)

    assert result == 50


def test_equity():
    acc = Account(1000)
    pnl = PnLService()

    acc.apply_trade(TradeEvent(side=TradeSide.BUY, price=10, quantity=10))  # cash = 900

    equity = pnl.calculate_equity(acc, current_price=20)

    assert equity == 900 + 200


def test_total_pnl():
    acc = Account(1000)
    pnl = PnLService()

    acc.apply_trade(TradeEvent(side=TradeSide.BUY, price=10, quantity=10))
    acc.apply_trade(TradeEvent(side=TradeSide.SELL, price=20, quantity=5))  # realized = 50

    total = pnl.calculate_total_pnl(acc, current_price=20)

    # unrealized = (20-10)*5 = 50
    # total = 50 + 50
    assert total == 100