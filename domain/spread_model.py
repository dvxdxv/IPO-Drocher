class FixedSpreadModel:
    def __init__(self, spread_pct: float = 0.00036):
        self.spread_pct = spread_pct

    def get_bid_ask(self, price: float):
        half_spread = price * self.spread_pct / 2
        bid = price - half_spread
        ask = price + half_spread
        return bid, ask