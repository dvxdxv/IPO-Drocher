"""
Session Service.

Responsible for:
- Final result calculation
- ROI
- Grade assignment
- Aggregated session summary

Stateless. Reads from Account + price.
"""

from domain.account import Account
from services.pnl_service import PnLService


class SessionService:
    def __init__(self, pnl_service: PnLService):
        self.pnl_service = pnl_service

    # --- core metrics ---

    def calculate_roi(self, account: Account, current_price: float) -> float:
        """
        Return on investment in percentage.
        """
        equity = self.pnl_service.calculate_equity(account, current_price)
        initial = account.initial_cash

        if initial == 0:
            return 0.0

        return ((equity - initial) / initial) * 100

    def assign_grade(self, roi: float) -> str:
        """
        Simple prop-style grading system.
        """

        if roi >= 50:
            return "A+"
        elif roi >= 30:
            return "A"
        elif roi >= 15:
            return "B"
        elif roi >= 5:
            return "C"
        elif roi >= 0:
            return "D"
        else:
            return "F"

    # --- final result ---

    def get_session_result(self, account: Account, current_price: float) -> dict:
        """
        Full session summary.
        """

        pnl_report = self.pnl_service.get_report(account, current_price)
        roi = self.calculate_roi(account, current_price)
        grade = self.assign_grade(roi)

        return {
            "initial_cash": account.initial_cash,
            "final_equity": pnl_report["equity"],
            "realized_pnl": pnl_report["realized_pnl"],
            "unrealized_pnl": pnl_report["unrealized_pnl"],
            "total_pnl": pnl_report["total_pnl"],
            "roi_percent": roi,
            "grade": grade,
            "win_rate": account.get_win_rate(),
            "total_trades": account.trade_count,
        }