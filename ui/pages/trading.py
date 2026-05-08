import streamlit as st
import time
from core.settings import AUTO_TICK_INTERVAL_SECONDS
from core.utils import now_utc
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

    if "last_auto_tick_ts" not in st.session_state:
        st.session_state.last_auto_tick_ts = time.time()

    if "auto_play" not in st.session_state:
        st.session_state.auto_play = True

    if (
        st.session_state.auto_play
        and not clock.is_paused
        and not clock.is_finished()
    ):
        now = time.time()
        elapsed = now - st.session_state.last_auto_tick_ts

        if elapsed >= AUTO_TICK_INTERVAL_SECONDS:
            if clock.tick():
                bus.publish(
                    MarketTickEvent(
                        timestamp=now_utc(),
                        index=clock.current_index,
                    ),
                    publisher="ui.trading.auto_tick",
                    metadata={"index": clock.current_index},
                )
            else:
                result = bus.publish(
                    MarketClosedEvent(timestamp=now_utc()),
                    publisher="ui.trading.auto_tick",
                )
                st.session_state.session_result = result

            st.session_state.last_auto_tick_ts = now
            st.rerun()

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
    col_auto, col_finish = st.columns(2)

    with col_auto:
        st.session_state.auto_play = st.toggle(
            "Auto Play",
            value=st.session_state.auto_play,
        )

    with col_finish:
        if st.button("Finish Session", width="stretch"):
            result = bus.publish(
                MarketClosedEvent(timestamp=now_utc()),
                publisher="ui.trading.finish_session",
            )
            st.session_state.session_result = result
            st.session_state.auto_play = False
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

        if st.button("Preview Trade", width="stretch", disabled=not can_preview):
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
            if st.button("Confirm Trade", width="stretch"):
                bus.publish(
                    TradeRequestedEvent(
                        timestamp=now_utc(),
                        side=pending["side"],
                        quantity=pending["quantity"],
                    ),
                    publisher=f"ui.trading.confirm_{pending['side'].value.lower()}",
                    metadata={
                        "side": pending["side"].value,
                        "quantity": pending["quantity"],
                        "price": pending["price"],
                    },
                )

                clock.resume()
                del st.session_state.pending_trade
                st.rerun()

        with col_cancel:
            if st.button("Cancel", width="stretch"):
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

        st.dataframe(rows, width="stretch")

    # --- Session Result ---
    if "session_result" in st.session_state:
        st.divider()
        st.subheader("Session Result")
        st.json(st.session_state.session_result)

    if (
        st.session_state.get("auto_play", True)
        and not clock.is_paused
        and not clock.is_finished()
    ):
        time.sleep(0.15)
        st.rerun()