"""
PnL Service.

Stateless service responsible for:
- Unrealized PnL
- Realized PnL
- Total PnL
- Equity calculation

This service does NOT mutate state.
It only reads from Account and external inputs (price).
"""

from domain.account import Account


class PnLService:
    def calculate_unrealized(self, account: Account, current_price: float) -> float:
        """
        Mark-to-market unrealized PnL.
        """
        if account.shares == 0:
            return 0.0

        return (current_price - account.avg_price) * account.shares

    def calculate_realized(self, account: Account) -> float:
        """
        Realized PnL accumulated from closed trades.
        """
        return account.realized_pnl

    def calculate_equity(self, account: Account, current_price: float) -> float:
        """
        Total account equity.
        """
        return account.cash + (account.shares * current_price)

    def calculate_total_pnl(self, account: Account, current_price: float) -> float:
        """
        Realized + Unrealized PnL.
        """
        return self.calculate_realized(account) + self.calculate_unrealized(
            account, current_price
        )

    def get_report(self, account: Account, current_price: float) -> dict:
        """
        Aggregated PnL report.
        """
        realized = self.calculate_realized(account)
        unrealized = self.calculate_unrealized(account, current_price)
        equity = self.calculate_equity(account, current_price)

        return {
            "realized_pnl": realized,
            "unrealized_pnl": unrealized,
            "total_pnl": realized + unrealized,
            "equity": equity,
        }