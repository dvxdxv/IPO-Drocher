import time

import plotly.graph_objects as go
import streamlit as st

from core.settings import AUTO_TICK_INTERVAL_SECONDS
from core.utils import now_utc
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

def _render_metric_card(label: str, value: str, css_class: str = "") -> None:
    st.markdown(
        f"""
        <div class="glass-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value {css_class}">{value}</div>
        </div>
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
    asset_name = st.session_state.get("asset", "IPO")
    equity = account.get_equity(price)
    unrealized_pnl = account.get_unrealized_pnl(price)
    total_pnl = account.realized_pnl + unrealized_pnl

    pnl_class = "positive" if total_pnl >= 0 else "negative"

    # --- Header ---
    st.markdown(
        f"""
        <h1 style="text-align:center; margin-bottom:0;">
            Trading • <span style="color:#00ff9d">{asset_name}</span>
        </h1>
        <p style="text-align:center; color:rgba(255,255,255,0.6);">
            Trader: {st.session_state.get("username", "-")}
        </p>
        """,
        unsafe_allow_html=True,
    )

    header_left, header_right = st.columns([3, 2])

    with header_left:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="muted">Market Price</div>
                <div class="ticker-price">${price:,.2f}</div>
                <div class="muted">Step: {clock.current_index}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with header_right:
        recent_prices = _get_recent_prices(market, 30)

        if len(recent_prices) > 1:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    y=recent_prices,
                    mode="lines",
                    line=dict(color="#00ff9d", width=3),
                )
            )
            fig.update_layout(
                height=140,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_visible=False,
                yaxis_visible=False,
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="muted">Chart</div>
                    <div class="metric-value">Waiting for ticks...</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    metric_cols = st.columns(4)

    with metric_cols[0]:
        _render_metric_card("Cash", f"${account.cash:,.2f}")

    with metric_cols[1]:
        _render_metric_card("Shares", f"{account.shares}")

    with metric_cols[2]:
        _render_metric_card("Equity", f"${equity:,.2f}")

    with metric_cols[3]:
        _render_metric_card("Total P&L", f"${total_pnl:,.2f}", pnl_class)

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
        st.markdown('<div class="trade-title">Trade</div>', unsafe_allow_html=True)

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

            st.markdown(
                f"""
                <div class="glass-card">
                    <div class="section-title">Trade Confirmation</div>
                    <div class="muted">Action</div>
                    <div class="metric-value">{label}</div>
                    <br>
                    <div class="muted">Execution Price</div>
                    <div class="metric-value">${execution_price:,.2f}</div>
                    <br>
                    <div class="muted">Estimated Value</div>
                    <div class="metric-value">${estimated_value:,.2f}</div>
                    <br>
                    <div class="muted">After Trade</div>
                    <div>Cash: ${account.cash:,.2f} → ${projected_cash:,.2f}</div>
                    <div>Shares: {account.shares} → {projected_shares}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

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
        st.markdown('<div class="section-title">Portfolio</div>', unsafe_allow_html=True)

        position_value = account.shares * price
        position_pct = (position_value / equity) * 100 if equity > 0 else 0

        _render_metric_card("Avg Price", f"${account.avg_price:,.2f}")
        st.write("")
        _render_metric_card("Position Value", f"${position_value:,.2f}")
        st.write("")
        _render_metric_card("Realized P&L", f"${account.realized_pnl:,.2f}")
        st.write("")
        _render_metric_card("Unrealized P&L", f"${unrealized_pnl:,.2f}")
        st.write("")
        _render_metric_card("Position Size", f"{position_pct:.1f}%")

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

            st.caption("Session is complete. You can review your trades below or start a new session.")

    if (
        st.session_state.get("auto_play", True)
        and not clock.is_paused
        and not clock.is_finished()
    ):
        time.sleep(0.15)
        st.rerun()