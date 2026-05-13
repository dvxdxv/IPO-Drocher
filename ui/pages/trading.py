import logging
import time

import streamlit as st

from core.settings import AUTO_TICK_INTERVAL_SECONDS
from core.utils import now_utc
from domain.models import TradeSide
from events.market_events import MarketClosedEvent, MarketTickEvent
from ui.state import get_engine

from ui.components.account_metrics import render_account_metrics
from ui.components.price_chart import render_price_chart
from ui.components.session_header import render_session_header
from ui.components.trade_review_dialog import render_trade_review_dialog

logger = logging.getLogger("ipo_drocher.ui.trading")


def apply_custom_css() -> None:
    """
    Keep page-level CSS empty.

    Header CSS belongs to session_header.py.
    Streamlit theme belongs to .streamlit/config.toml.
    """

    return


def _debug_trade_state() -> dict:
    return {
        "pending_side": st.session_state.get("pending_side"),
        "pending_label": st.session_state.get("pending_label"),
        "trade_review_open": st.session_state.get("trade_review_open"),
        "trade_review_qty": st.session_state.get("trade_review_qty"),
        "resume_after_trade_review": st.session_state.get("resume_after_trade_review"),
        "auto_play": st.session_state.get("auto_play"),
    }


def _format_timestamp(timestamp) -> str:
    if timestamp is None:
        return "-"

    if hasattr(timestamp, "strftime"):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

    return str(timestamp)


def _init_trading_state() -> None:
    st.session_state.setdefault("last_auto_tick_ts", time.time())
    st.session_state.setdefault("auto_play", True)
    st.session_state.setdefault("trade_review_open", False)
    st.session_state.setdefault("resume_after_trade_review", False)


def _open_trade_review(clock, side: TradeSide, label: str) -> None:
    """
    Open order review modal and stop simulation immediately.
    """

    logger.info(
        "OPEN_TRADE_REVIEW | side=%s | label=%s | paused_before=%s | state=%s",
        side,
        label,
        clock.is_paused,
        _debug_trade_state(),
    )

    clock.pause()

    st.session_state.auto_play = False
    st.session_state.trade_review_open = True
    st.session_state.resume_after_trade_review = False
    st.session_state.last_auto_tick_ts = time.time()

    for key in (
        "trade_review_qty",
        "trade_review_qty_buy",
        "trade_review_qty_sell",
    ):
        st.session_state.pop(key, None)

    st.session_state.pending_side = side
    st.session_state.pending_label = label

    logger.info(
        "OPEN_TRADE_REVIEW_DONE | paused_after=%s | state=%s",
        clock.is_paused,
        _debug_trade_state(),
    )


def _resume_after_trade_review_if_needed(clock) -> None:
    """
    Resume simulation only after dialog state has been closed.
    """

    if not st.session_state.get("resume_after_trade_review", False):
        return

    if st.session_state.get("trade_review_open", False):
        logger.warning(
            "RESUME_SKIPPED | reason=dialog_still_open | state=%s",
            _debug_trade_state(),
        )
        return

    logger.info(
        "RESUME_AFTER_TRADE_REVIEW | paused_before=%s | state=%s",
        clock.is_paused,
        _debug_trade_state(),
    )

    clock.resume()
    st.session_state.auto_play = True
    st.session_state.last_auto_tick_ts = time.time()
    st.session_state.resume_after_trade_review = False

    toast_message = st.session_state.pop("trade_toast", None)
    if toast_message:
        st.toast(toast_message, icon="✅")

    logger.info(
        "RESUME_AFTER_TRADE_REVIEW_DONE | paused_after=%s | state=%s",
        clock.is_paused,
        _debug_trade_state(),
    )


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


def _run_autoplay_if_due(bus, clock) -> None:
    """
    Run at most one simulation tick per Streamlit rerun.
    """

    if not st.session_state.get("auto_play", True):
        return

    if st.session_state.get("trade_review_open", False):
        return

    if clock.is_paused or clock.is_finished():
        return

    now = time.time()
    elapsed = now - st.session_state.last_auto_tick_ts

    if elapsed < AUTO_TICK_INTERVAL_SECONDS:
        return

    _publish_auto_tick(bus, clock)
    st.session_state.last_auto_tick_ts = now
    st.rerun()


def _render_time_controls(bus) -> None:
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


def _render_trade_panel(clock, account) -> None:
    st.subheader("Trade")

    buy_col, sell_col, spacer_col = st.columns([1, 1, 2])

    with buy_col:
        if st.button("BUY", type="primary", width="stretch", key="buy_button"):
            _open_trade_review(clock, TradeSide.BUY, "BUY")
            st.rerun()

    with sell_col:
        sell_disabled = account.shares <= 0

        if st.button(
            "SELL",
            width="stretch",
            key="sell_button",
            disabled=sell_disabled,
        ):
            _open_trade_review(clock, TradeSide.SELL, "SELL")
            st.rerun()

    if account.shares <= 0:
        st.caption("SELL is disabled because you do not hold shares.")

def _render_transactions(account) -> None:
    st.divider()
    st.subheader("Transactions")

    trades = account.trades

    if not trades:
        st.info("No trades executed yet.")
        return

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


def _render_session_result() -> None:
    if "session_result" not in st.session_state or not st.session_state.session_result:
        return

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


def _render_trade_review_dialog_if_needed(bus, account, market) -> None:
    should_open = (
        st.session_state.get("trade_review_open", False)
        and "pending_side" in st.session_state
    )

    logger.info(
        "DIALOG_GATE | should_open=%s | state=%s",
        should_open,
        _debug_trade_state(),
    )

    if should_open:
        render_trade_review_dialog(bus, account, market)


def _rerun_for_autoplay_if_needed(clock) -> None:
    if (
        st.session_state.get("auto_play", True)
        and not st.session_state.get("trade_review_open", False)
        and not clock.is_paused
        and not clock.is_finished()
    ):
        time.sleep(0.15)
        st.rerun()


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

    _init_trading_state()
    _resume_after_trade_review_if_needed(clock)
    _run_autoplay_if_due(bus, clock)

    price = market.get_current_price()

    render_session_header(account, clock, market)
    st.write("")

    render_price_chart(
        market,
        window=60,
        height=220,
        interactive=False,
    )

    metrics = render_account_metrics(account, price)
    equity = metrics["equity"]
    unrealized_pnl = metrics["unrealized_pnl"]

    st.write("")

    _render_time_controls(bus)

    st.divider()

    _render_trade_panel(clock, account)

    _render_trade_review_dialog_if_needed(bus, account, market)

    _render_transactions(account)
    _render_session_result()

    _rerun_for_autoplay_if_needed(clock)