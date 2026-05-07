from domain.account import Account
from domain.models import TradeSide


class TradingService:
    def __init__(self, account: Account):
        self.account = account

    def validate(self, side: TradeSide, quantity: int, price: float):
        if quantity <= 0:
            return False, "Quantity must be positive"

        if side == TradeSide.BUY:
            cost = quantity * price
            if cost > self.account.cash:
                return False, "Insufficient cash"

        elif side == TradeSide.SELL:
            if quantity > self.account.position.quantity:
                return False, "Insufficient shares"

        else:
            return False, "Invalid side"

        return True, None

    def simulate(self, side: TradeSide, quantity: int, price: float):
        """
        Returns projected state AFTER trade (does not mutate account)
        """
        cash = self.account.cash
        qty = self.account.position.quantity
        avg = self.account.position.avg_price

        if side == TradeSide.BUY:
            total_cost = quantity * price
            new_qty = qty + quantity

            if new_qty == 0:
                new_avg = 0
            else:
                new_avg = ((qty * avg) + (quantity * price)) / new_qty

            return {
                "cash": cash - total_cost,
                "shares": new_qty,
                "avg_price": new_avg,
            }

        else:  # SELL
            total_value = quantity * price
            new_qty = qty - quantity

            return {
                "cash": cash + total_value,
                "shares": new_qty,
                "avg_price": avg if new_qty > 0 else 0,
            }