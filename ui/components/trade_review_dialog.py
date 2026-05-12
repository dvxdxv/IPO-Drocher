import logging

import streamlit as st

from core.utils import now_utc
from domain.models import TradeSide
from events.trade_events import TradeRequestedEvent


logger = logging.getLogger("ipo_drocher.ui.trade_review_dialog")


def _debug_state() -> dict:
    return {
        "pending_side": st.session_state.get("pending_side"),
        "pending_label": st.session_state.get("pending_label"),
        "trade_review_open": st.session_state.get("trade_review_open"),
        "trade_review_qty_buy": st.session_state.get("trade_review_qty_buy"),
        "trade_review_qty_sell": st.session_state.get("trade_review_qty_sell"),
        "resume_after_trade_review": st.session_state.get("resume_after_trade_review"),
        "auto_play": st.session_state.get("auto_play"),
    }


def _close_trade_review() -> None:
    """
    Close dialog state only.

    Do not resume clock here.
    The main trading page resumes clock after the dialog is no longer rendered.
    """

    logger.info("CLOSE_TRADE_REVIEW_START | state=%s", _debug_state())

    st.session_state.trade_review_open = False
    st.session_state.resume_after_trade_review = True

    for key in (
        "pending_side",
        "pending_label",
        "trade_review_qty",
        "trade_review_qty_buy",
        "trade_review_qty_sell",
    ):
        st.session_state.pop(key, None)


    logger.info("CLOSE_TRADE_REVIEW_DONE | state=%s", _debug_state())


def _get_order_quantity(side: TradeSide, account) -> int:
    key = f"trade_review_qty_{side.value.lower()}"

    if side == TradeSide.SELL:
        max_qty = max(account.shares, 1)
        default_qty = max(1, min(account.shares, 10))

        return st.number_input(
            "Quantity",
            min_value=1,
            max_value=max_qty,
            value=default_qty,
            step=1,
            key=key,
        )

    return st.number_input(
        "Quantity",
        min_value=1,
        value=10,
        step=1,
        key=key,
    )


@st.dialog("Order Review", dismissible=False)
def render_trade_review_dialog(bus, account, market) -> None:
    """
    Trade review modal.

    Clock is intentionally not resumed here.
    This dialog only confirms/cancels and updates session_state.
    """

    logger.info("DIALOG_RENDER_START | state=%s", _debug_state())

    if not st.session_state.get("trade_review_open", False):
        logger.info("DIALOG_RENDER_STOPPED | reason=trade_review_open_false")
        st.stop()

    if "pending_side" not in st.session_state:
        logger.warning("DIALOG_RENDER_STOPPED | reason=no_pending_side | state=%s", _debug_state())
        st.session_state.trade_review_open = False
        st.stop()

    side: TradeSide = st.session_state.pending_side
    label: str = st.session_state.pending_label
    asset_name = st.session_state.get("asset", "IPO")

    execution_price = market.get_execution_price(side)
    qty = _get_order_quantity(side, account)

    estimated_value = qty * execution_price

    if side == TradeSide.BUY:
        projected_cash = account.cash - estimated_value
        projected_shares = account.shares + qty
        trade_pnl = 0.0
    else:
        projected_cash = account.cash + estimated_value
        projected_shares = account.shares - qty
        trade_pnl = qty * (execution_price - account.avg_price)

    can_confirm = True

    if side == TradeSide.BUY and projected_cash < 0:
        can_confirm = False
    elif side == TradeSide.SELL and qty > account.shares:
        can_confirm = False

    st.markdown(f"### {label} {asset_name}")

    st.markdown(
        f"""
**{label} {qty} {asset_name} shares for ${estimated_value:,.2f}**

Price: **${execution_price:,.2f}**  
Quantity: **{qty} shares**
"""
    )

    if not can_confirm:
        if side == TradeSide.BUY:
            st.error("Insufficient cash")
        else:
            st.error("Insufficient shares")

    st.divider()
    st.markdown("#### Portfolio Impact")

    col_before, col_after = st.columns(2)

    with col_before:
        st.metric("Cash Before", f"${account.cash:,.2f}")
        st.metric("Shares Before", account.shares)

    with col_after:
        st.metric("Cash After", f"${projected_cash:,.2f}")
        st.metric("Shares After", projected_shares)

    if side == TradeSide.SELL:
        st.metric("Realized P&L on Trade", f"${trade_pnl:,.2f}")

    st.divider()

    confirm_col, cancel_col = st.columns(2)

    with confirm_col:
        confirm_clicked = st.button(
            f"Confirm {label}",
            type="primary",
            width="stretch",
            disabled=not can_confirm,
            key="confirm_trade_button",
        )

    with cancel_col:
        cancel_clicked = st.button(
            "Cancel",
            width="stretch",
            key="cancel_trade_button",
        )

    if confirm_clicked:
        logger.info(
            "CONFIRM_CLICKED | side=%s | qty=%s | price=%s | cash_before=%s | shares_before=%s | state=%s",
            side,
            qty,
            execution_price,
            account.cash,
            account.shares,
            _debug_state(),
        )

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
                "estimated_value": estimated_value,
            },
        )

        logger.info(
            "CONFIRM_EXECUTED | cash_after=%s | shares_after=%s | state=%s",
            account.cash,
            account.shares,
            _debug_state(),
        )

        st.session_state.trade_toast = (
            f"{label} {qty} {asset_name} shares executed at ${execution_price:,.2f}"
        )

        _close_trade_review()
        st.rerun(scope="app")

    if cancel_clicked:
        logger.info("CANCEL_CLICKED | state=%s", _debug_state())

        st.session_state.trade_toast = "Trade draft cancelled."

        _close_trade_review()
        st.rerun(scope="app")