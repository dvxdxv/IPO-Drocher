import time

import plotly.graph_objects as go
import streamlit as st

from core.settings import AUTO_TICK_INTERVAL_SECONDS
from core.utils import (
    now_utc,
    format_duration_from_minutes,
    format_market_datetime,
)
from domain.models import TradeSide
from events.market_events import MarketClosedEvent, MarketTickEvent
from events.trade_events import TradeRequestedEvent
from ui.state import get_engine


def apply_custom_css() -> None:
    st.markdown(
        """
        <style>
            .app-title {
                font-size: 2.8rem;
                font-weight: 800;
                text-align: center;
                margin-bottom: 0.25rem;
            }

            .app-subtitle {
                text-align: center;
                opacity: 0.75;
                margin-bottom: 2rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _get_recent_prices(market, window: int = 30):
    if hasattr(market, "get_recent_prices"):
        return market.get_recent_prices(window)

    return [market.get_current_price()]


def _format_timestamp(timestamp) -> str:
    if timestamp is None:
        return "-"

    if hasattr(timestamp, "strftime"):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

    return str(timestamp)


def _start_trade_draft(clock, side: TradeSide, label: str) -> None:
    clock.pause()
    st.session_state.auto_play = False
    st.session_state.last_auto_tick_ts = time.time()
    st.session_state.pending_side = side
    st.session_state.pending_label = label


def _clear_trade_draft(clock, resume: bool = True) -> None:
    if resume:
        clock.resume()
        st.session_state.auto_play = True

    st.session_state.last_auto_tick_ts = time.time()

    for key in ("pending_side", "pending_label"):
        if key in st.session_state:
            del st.session_state[key]


def _publish_auto_tick(bus, clock) -> None:
    if clock.tick():
        bus.publish(
            MarketTickEvent(
                timestamp=now_utc(),
                index=clock.current_index,
            ),
            publisher="ui.trading.auto_tick",
            metadata={"index": clock.current_index},
        )
        return

    result = bus.publish(
        MarketClosedEvent(timestamp=now_utc()),
        publisher="ui.trading.auto_tick",
    )

    st.session_state.session_result = result
    st.session_state.auto_play = False


def render_compact_header(account, clock, market) -> None:
    asset_name = st.session_state.get("asset", "IPO")
    trader_name = st.session_state.get("username", "-")

    price = market.get_current_price()

    current_time = format_market_datetime(market.get_current_timestamp())
    elapsed = format_duration_from_minutes(market.get_elapsed_steps())
    remaining = format_duration_from_minutes(market.get_remaining_steps())

    if clock.is_finished():
        status = "Finished"
    elif clock.is_paused:
        status = "Paused"
    else:
        status = "Running"

    with st.container(border=True):
        row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(
            [1.1, 1.2, 1.1, 2.4]
        )

        with row1_col1:
            st.markdown(f"### {asset_name}")

        with row1_col2:
            st.markdown(f"### ${price:,.2f}")

        with row1_col3:
            st.markdown(f"### {status}")

        with row1_col4:
            st.markdown(f"**NYC:** {current_time}")

        row2_col1, row2_col2, row2_col3 = st.columns([1.3, 1.7, 1.7])

        with row2_col1:
            st.caption(f"Trader: {trader_name}")

        with row2_col2:
            st.caption(f"Session Elapsed: {elapsed}")

        with row2_col3:
            st.caption(f"Time Left: {remaining}")


def render_trading_page() -> None:
    apply_custom_css()

    engine = get_engine()

    if not engine:
        st.warning("Initialize session first")
        st.stop()

    bus = engine["bus"]
    clock = engine["clock"]
    account = engine["account"]
    market = engine["market"]

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
            _publish_auto_tick(bus, clock)
            st.session_state.last_auto_tick_ts = now
            st.rerun()

    price = market.get_current_price()
    equity = account.get_equity(price)
    unrealized_pnl = account.get_unrealized_pnl(price)
    total_pnl = account.realized_pnl + unrealized_pnl

    # --- Header ---
    render_compact_header(account, clock, market)

    st.write("")

    # --- Chart ---
    recent_prices = _get_recent_prices(market, 60)

    with st.container(border=True):
        st.markdown("#### Price Chart")

        if len(recent_prices) > 1:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    y=recent_prices,
                    mode="lines",
                    line=dict(color="#22c55e", width=3),
                )
            )
            fig.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_visible=False,
                yaxis_visible=False,
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Waiting for market ticks...")

    st.write("")

    # --- Key Metrics ---
    metric_cols = st.columns(4)

    with metric_cols[0]:
        st.metric("Cash", f"${account.cash:,.2f}")

    with metric_cols[1]:
        st.metric("Shares", f"{account.shares}")

    with metric_cols[2]:
        st.metric("Equity", f"${equity:,.2f}")

    with metric_cols[3]:
        st.metric("Total P&L", f"${total_pnl:,.2f}")

    st.write("")

    # --- Time Controls ---
    control_left, control_right = st.columns([1, 1])

    with control_left:
        st.session_state.auto_play = st.toggle(
            "Auto Play",
            value=st.session_state.auto_play,
        )

    with control_right:
        if st.button("Finish Session", width="stretch"):
            result = bus.publish(
                MarketClosedEvent(timestamp=now_utc()),
                publisher="ui.trading.finish_session",
            )
            st.session_state.session_result = result
            st.session_state.auto_play = False
            st.rerun()

    st.divider()

    # --- Main Layout ---
    trade_col, portfolio_col = st.columns([2, 1])

    with trade_col:
        st.subheader("Trade")

        buy_col, sell_col = st.columns(2)

        with buy_col:
            if st.button("BUY", type="primary", width="stretch", key="buy_button"):
                _start_trade_draft(clock, TradeSide.BUY, "BUY")
                st.rerun()

        with sell_col:
            sell_disabled = account.shares <= 0

            if st.button(
                "SELL",
                width="stretch",
                key="sell_button",
                disabled=sell_disabled,
            ):
                _start_trade_draft(clock, TradeSide.SELL, "SELL")
                st.rerun()

        if account.shares <= 0:
            st.caption("SELL is disabled because you do not hold shares.")

        if "pending_side" in st.session_state:
            side = st.session_state.pending_side
            label = st.session_state.pending_label

            execution_price = market.get_execution_price(side)

            if side == TradeSide.SELL:
                max_qty = max(account.shares, 1)
                default_qty = max(1, min(account.shares, 10))
                qty = st.number_input(
                    "Quantity (shares)",
                    min_value=1,
                    max_value=max_qty,
                    value=default_qty,
                    step=1,
                )
            else:
                qty = st.number_input(
                    "Quantity (shares)",
                    min_value=1,
                    value=10,
                    step=1,
                )

            estimated_value = qty * execution_price

            if side == TradeSide.BUY:
                projected_cash = account.cash - estimated_value
                projected_shares = account.shares + qty
            else:
                projected_cash = account.cash + estimated_value
                projected_shares = account.shares - qty

            with st.container(border=True):
                st.markdown(f"### Trade Confirmation: {label}")
                st.write(f"Execution Price: **${execution_price:,.2f}**")
                st.write(f"Estimated Value: **${estimated_value:,.2f}**")
                st.write(f"Cash: ${account.cash:,.2f} → ${projected_cash:,.2f}")
                st.write(f"Shares: {account.shares} → {projected_shares}")

            if side == TradeSide.BUY and projected_cash < 0:
                st.error("Insufficient cash")
                can_confirm = False
            elif side == TradeSide.SELL and qty > account.shares:
                st.error("Insufficient shares")
                can_confirm = False
            else:
                can_confirm = True

            confirm_col, cancel_col = st.columns(2)

            with confirm_col:
                if st.button(
                    f"Confirm {label}",
                    type="primary",
                    width="stretch",
                    disabled=not can_confirm,
                ):
                    bus.publish(
                        TradeRequestedEvent(
                            timestamp=now_utc(),
                            side=side,
                            quantity=qty,
                        ),
                        publisher=f"ui.trading.confirm_{side.value.lower()}",
                        metadata={
                            "side": side.value,
                            "quantity": qty,
                            "price": execution_price,
                        },
                    )

                    _clear_trade_draft(clock, resume=True)
                    st.rerun()

            with cancel_col:
                if st.button("Cancel", width="stretch"):
                    _clear_trade_draft(clock, resume=True)
                    st.rerun()

    with portfolio_col:
        st.subheader("Portfolio")

        position_value = account.shares * price
        position_pct = (position_value / equity) * 100 if equity > 0 else 0

        with st.container(border=True):
            st.metric("Avg Price", f"${account.avg_price:,.2f}")
            st.metric("Position Value", f"${position_value:,.2f}")
            st.metric("Realized P&L", f"${account.realized_pnl:,.2f}")
            st.metric("Unrealized P&L", f"${unrealized_pnl:,.2f}")
            st.metric("Position Size", f"{position_pct:.1f}%")

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
                    "Side": trade.side.value
                    if hasattr(trade.side, "value")
                    else str(trade.side),
                    "Qty": trade.quantity,
                    "Price": f"${trade.price:,.2f}",
                    "Timestamp": _format_timestamp(trade.timestamp),
                }
            )

        st.dataframe(rows, width="stretch", hide_index=True)

    # --- Session Result ---
    if "session_result" in st.session_state and st.session_state.session_result:
        result = st.session_state.session_result

        final_equity = result.get("final_equity", 0.0)
        total_pnl = result.get("total_pnl", 0.0)
        realized_pnl = result.get("realized_pnl", 0.0)
        unrealized_pnl = result.get("unrealized_pnl", 0.0)
        roi_percent = result.get("roi_percent", 0.0)
        grade = result.get("grade", "-")
        win_rate = result.get("win_rate", 0.0)
        total_trades = result.get("total_trades", 0)

        pnl_sign = "+" if total_pnl >= 0 else ""
        roi_sign = "+" if roi_percent >= 0 else ""

        st.divider()
        st.subheader("Session Result")

        with st.container(border=True):
            st.markdown(f"## Grade: `{grade}`")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Final Equity", f"${final_equity:,.2f}")

            with col2:
                st.metric("Total P&L", f"{pnl_sign}${total_pnl:,.2f}")

            with col3:
                st.metric("ROI", f"{roi_sign}{roi_percent:.2f}%")

            st.divider()

            col4, col5, col6 = st.columns(3)

            with col4:
                st.metric("Realized P&L", f"${realized_pnl:,.2f}")

            with col5:
                st.metric("Unrealized P&L", f"${unrealized_pnl:,.2f}")

            with col6:
                st.metric("Win Rate", f"{win_rate:.1f}%")

            st.markdown(f"**Total Trades:** {total_trades}")

            st.caption(
                "Session is complete. You can review your trades below or start a new session."
            )

    if (
        st.session_state.get("auto_play", True)
        and not clock.is_paused
        and not clock.is_finished()
    ):
        time.sleep(0.15)
        st.rerun()