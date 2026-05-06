import streamlit as st
from datetime import datetime, timezone

from domain.models import TradeSide
from events.trade_events import TradeRequestedEvent
from events.market_events import MarketTickEvent, MarketClosedEvent
from ui.state import get_engine


def render_trading_page():
    engine = get_engine()

    if not engine:
        st.warning("Initialize session first")
        st.stop()

    bus = engine["bus"]
    clock = engine["clock"]
    account = engine["account"]
    market = engine["market"]

    price = market.get_current_price()

    # --- Header ---
    col1, col2, col3 = st.columns(3)

    col1.write(f"Trader: {st.session_state.get('username', '-')}")
    col2.write("NYC: TODO")
    col3.write(f"Step: {clock.current_index}")

    # --- Basic account metrics ---
    equity = account.get_equity(price)
    unrealized_pnl = account.get_unrealized_pnl(price)
    total_pnl = account.realized_pnl + unrealized_pnl

    st.markdown(
        f"### Equity: ${equity:,.2f} | "
        f"P&L: ${total_pnl:,.2f} | "
        f"Price: ${price:,.2f}"
    )

    # --- Time controls ---
    col_tick, col_finish = st.columns(2)

    with col_tick:
        if st.button("Next Tick", use_container_width=True):
            if clock.tick():
                bus.publish(
                    MarketTickEvent(
                        timestamp=datetime.now(timezone.utc),
                        index=clock.current_index,
                    )
                )
            else:
                result = bus.publish(
                    MarketClosedEvent(
                        timestamp=datetime.now(timezone.utc)
                    )
                )
                st.session_state.session_result = result

            st.rerun()

    with col_finish:
        if st.button("Finish Session", use_container_width=True):
            result = bus.publish(
                MarketClosedEvent(
                    timestamp=datetime.now(timezone.utc)
                )
            )
            st.session_state.session_result = result
            st.rerun()

    st.divider()

    # --- Layout ---
    left, right = st.columns([2, 1])

    # --- Trade Panel ---
    with left:
        st.subheader("Trade")

        side_label = st.radio(
            "Action",
            ["Buy", "Sell"],
            horizontal=True,
        )

        qty = st.number_input(
            "Shares",
            min_value=1,
            value=10,
            step=1,
        )

        side = TradeSide[side_label.upper()]
        execution_price = market.get_execution_price(side)

        estimated_value = qty * execution_price

        st.write(f"Execution Price: ${execution_price:,.2f}")
        st.write(f"Estimated Value: ${estimated_value:,.2f}")

        if side == TradeSide.BUY:
            projected_cash = account.cash - estimated_value
            projected_shares = account.shares + qty
        else:
            projected_cash = account.cash + estimated_value
            projected_shares = account.shares - qty

        st.markdown("#### After Trade Preview")
        st.write(f"Cash: ${account.cash:,.2f} → ${projected_cash:,.2f}")
        st.write(f"Shares: {account.shares} → {projected_shares}")

        if side == TradeSide.BUY and projected_cash < 0:
            st.error("Insufficient cash")
            can_preview = False
        elif side == TradeSide.SELL and qty > account.shares:
            st.error("Insufficient shares")
            can_preview = False
        else:
            can_preview = True

        if st.button("Preview Trade", use_container_width=True, disabled=not can_preview):
            clock.pause()
            st.session_state.pending_trade = {
                "side": side,
                "side_label": side_label,
                "quantity": qty,
                "price": execution_price,
                "estimated_value": estimated_value,
                "projected_cash": projected_cash,
                "projected_shares": projected_shares,
            }
            st.rerun()

    # --- Portfolio Impact ---
    with right:
        st.subheader("Portfolio")

        st.metric("Cash", f"${account.cash:,.2f}")
        st.metric("Shares", account.shares)
        st.metric("Avg Price", f"${account.avg_price:,.2f}")
        st.metric("Realized P&L", f"${account.realized_pnl:,.2f}")
        st.metric("Unrealized P&L", f"${unrealized_pnl:,.2f}")

        if account.initial_cash > 0:
            position_value = account.shares * price
            position_pct = (position_value / equity) * 100 if equity > 0 else 0
            st.metric("Position Size", f"{position_pct:.1f}%")

    # --- Confirmation Section ---
    if "pending_trade" in st.session_state:
        st.divider()

        pending = st.session_state.pending_trade

        st.warning(
            f"Confirm {pending['side_label']} "
            f"{pending['quantity']} shares at "
            f"${pending['price']:,.2f}?"
        )

        col_confirm, col_cancel = st.columns(2)

        with col_confirm:
            if st.button("Confirm Trade", use_container_width=True):
                bus.publish(
                    TradeRequestedEvent(
                        timestamp=datetime.now(timezone.utc),
                        side=pending["side"],
                        quantity=pending["quantity"],
                    )
                )

                clock.resume()
                del st.session_state.pending_trade
                st.rerun()

        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                clock.resume()
                del st.session_state.pending_trade
                st.rerun()

    # --- Transactions ---
    st.divider()
    st.subheader("Transactions")

    trades = account.trades

    if not trades:
        st.info("No trades executed yet.")
    else:
        rows = []

        for trade in trades:
            rows.append(
                {
                    "Side": trade.side.value if hasattr(trade.side, "value") else str(trade.side),
                    "Qty": trade.quantity,
                    "Price": trade.price,
                    "Timestamp": trade.timestamp,
                }
            )

        st.dataframe(rows, use_container_width=True)

    # --- Session Result ---
    if "session_result" in st.session_state:
        st.divider()
        st.subheader("Session Result")
        st.json(st.session_state.session_result)