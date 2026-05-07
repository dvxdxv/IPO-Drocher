import pytest
from domain.account import Account
from domain.models import TradeEvent


def test_apply_trade_buy():
    acc = Account(1000)

    trade = TradeEvent(side="BUY", price=10, quantity=10)
    acc.apply_trade(trade)

    assert acc.cash == 900
    assert acc.position.quantity == 10


def test_avg_price():
    acc = Account(1000)

    acc.apply_trade(TradeEvent("BUY", 10, 10))  # 100
    acc.apply_trade(TradeEvent("BUY", 20, 10))  # 200

    assert acc.position.quantity == 20
    assert acc.position.avg_price == 15


def test_cash_update_sell():
    acc = Account(1000)

    acc.apply_trade(TradeEvent("BUY", 10, 10))   # -100
    acc.apply_trade(TradeEvent("SELL", 20, 5))   # +100

    assert acc.cash == 1000
    assert acc.position.quantity == 5


def test_sell_more_than_owned():
    acc = Account(1000)

    acc.apply_trade(TradeEvent("BUY", 10, 5))

    with pytest.raises(ValueError):
        acc.apply_trade(TradeEvent("SELL", 10, 10))