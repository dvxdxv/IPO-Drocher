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

    pnl_row = ""
    if side == TradeSide.SELL:
        pnl_color = "#22c55e" if trade_pnl >= 0 else "#ef4444"
        pnl_row = f"""
        <div class="tr-row">
            <span class="tr-label">Realized P&L</span>
            <span class="tr-value" style="color:{pnl_color}">${trade_pnl:,.2f}</span>
        </div>
        """

    st.markdown(f"""
    <style>
    .tr-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:6px 12px; margin:8px 0; }}
    .tr-cell {{ background:rgba(255,255,255,0.04); border-radius:8px; padding:8px 10px; }}
    .tr-cell-label {{ font-size:0.7rem; opacity:0.6; margin-bottom:2px; }}
    .tr-cell-value {{ font-size:1rem; font-weight:700; }}
    .tr-row {{ display:flex; justify-content:space-between; align-items:center; padding:6px 0; }}
    .tr-label {{ font-size:0.8rem; opacity:0.7; }}
    .tr-value {{ font-size:0.95rem; font-weight:700; }}
    </style>

    **Portfolio Impact**

    <div class="tr-grid">
        <div class="tr-cell">
            <div class="tr-cell-label">Cash Before</div>
            <div class="tr-cell-value">${account.cash:,.2f}</div>
        </div>
        <div class="tr-cell">
            <div class="tr-cell-label">Cash After</div>
            <div class="tr-cell-value">${projected_cash:,.2f}</div>
        </div>
        <div class="tr-cell">
            <div class="tr-cell-label">Shares Before</div>
            <div class="tr-cell-value">{account.shares}</div>
        </div>
        <div class="tr-cell">
            <div class="tr-cell-label">Shares After</div>
            <div class="tr-cell-value">{projected_shares}</div>
        </div>
    </div>
    
    """, unsafe_allow_html=True)
    if side == TradeSide.SELL:
        pnl_color = "#22c55e" if trade_pnl >= 0 else "#ef4444"
        st.markdown(f"""
        <div class="tr-row">
            <span class="tr-label">Realized P&L</span>
            <span class="tr-value" style="color:{pnl_color}">${trade_pnl:,.2f}</span>
        </div>
        """, unsafe_allow_html=True)

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