from domain.account import Account
from domain.models import TradeEvent, TradeSide
from services.pnl_service import PnLService
from services.session_service import SessionService


def test_roi_calculation():
    acc = Account(1000)
    pnl = PnLService()
    session = SessionService(pnl)

    acc.apply_trade(TradeEvent(TradeSide.BUY, 10, 10))  # spend 100

    roi = session.calculate_roi(acc, current_price=20)

    # equity = 900 + 200 = 1100 → +10%
    assert round(roi, 2) == 10.0


def test_grade_assignment():
    pnl = PnLService()
    session = SessionService(pnl)

    assert session.assign_grade(55) == "A+"
    assert session.assign_grade(35) == "A"
    assert session.assign_grade(20) == "B"
    assert session.assign_grade(10) == "C"
    assert session.assign_grade(2) == "D"
    assert session.assign_grade(-5) == "F"


def test_full_session_result():
    acc = Account(1000)
    pnl = PnLService()
    session = SessionService(pnl)

    acc.apply_trade(TradeEvent(TradeSide.BUY, 10, 10))
    acc.apply_trade(TradeEvent(TradeSide.SELL, 20, 5))  # realized +50

    result = session.get_session_result(acc, current_price=20)

    assert result["realized_pnl"] == 50
    assert result["final_equity"] > 1000
    assert "grade" in result