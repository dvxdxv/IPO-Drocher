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
    Page-level CSS only.

    Header structure belongs to session_header.py.
    Streamlit global theme belongs to .streamlit/config.toml.
    """
    st.markdown(
        """
        <style>
            /* =========================
               Page spacing
               ========================= */

            .block-container {
                padding-top: 3rem !important;
                padding-bottom: 5.5rem !important;
            }

            @media (max-width: 768px) {
                .block-container {
                    padding-top: 0.5rem !important;
                    padding-left: 1rem !important;
                    padding-right: 1rem !important;
                    padding-bottom: 3.5rem !important;
                }

                h1, h2, h3 {
                    margin-top: 0.35rem !important;
                    margin-bottom: 0.45rem !important;
                }

                div[data-testid="stVerticalBlock"] {
                    gap: 0.45rem !important;
                }
            }


            /* =========================
               Sticky compact header
               session_header.py renders .session-header
               ========================= */

            header[data-testid="stHeader"] 
            { display: none !important; }
               
            @media (max-width: 768px) {
                .session-header {
                    position: sticky !important;
                    top: 3.4rem !important;
                    z-index: 999 !important;
                    background: rgba(15, 23, 42, 0.94) !important;
                    backdrop-filter: blur(12px) !important;
                    -webkit-backdrop-filter: blur(12px) !important;
                    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25) !important;
                }
            }

            /* =========================
            IPO Trader Dashboard
            ========================= */

            .trader-dashboard {
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 12px;
                padding: 1rem;
                margin-top: 0.7rem;
                margin-bottom: 0.8rem;
                background: rgba(255, 255, 255, 0.02);
            }

            .dashboard-title {
                font-size: 1.15rem;
                font-weight: 800;
                margin-bottom: 0.9rem;
            }

            .dashboard-grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 1rem 1.2rem;
            }

            .dashboard-cell-label {
                font-size: 0.78rem;
                opacity: 0.68;
                margin-bottom: 0.25rem;
            }

            .dashboard-cell-value {
                font-size: 1.35rem;
                font-weight: 800;
                line-height: 1.15;
            }

            @media (max-width: 768px) {
                .trader-dashboard {
                    padding: 0.85rem;
                    margin-top: 0.5rem;
                    margin-bottom: 0.6rem;
                }

                .dashboard-title {
                    font-size: 1.05rem;
                    margin-bottom: 0.75rem;
                }

                .dashboard-grid {
                    grid-template-columns: repeat(2, 1fr);
                    gap: 0.75rem 1rem;
                }

                .dashboard-cell-label {
                    font-size: 0.72rem;
                }

                .dashboard-cell-value {
                    font-size: 1.05rem;
                }
            }
            /* =========================
               Trade action buttons
               ========================= */

            .st-key-sell_button button {
                background-color: #dc2626 !important;
                color: #ffffff !important;
                border: 1px solid #ef4444 !important;
                font-weight: 700 !important;
            }

            .st-key-sell_button button:hover {
                background-color: #ef4444 !important;
                color: #ffffff !important;
                border-color: #f87171 !important;
            }

            .st-key-sell_button button:disabled {
                background-color: rgba(127, 29, 29, 0.35) !important;
                color: rgba(255, 255, 255, 0.45) !important;
                border: 1px solid rgba(248, 113, 113, 0.35) !important;
            }

            .st-key-finish_session_button button {
                background-color: rgba(37, 99, 235, 0.18) !important;
                color: #bfdbfe !important;
                border: 1px solid rgba(96, 165, 250, 0.75) !important;
                font-weight: 700 !important;
            }

            .st-key-finish_session_button button:hover {
                background-color: rgba(37, 99, 235, 0.34) !important;
                color: #ffffff !important;
                border-color: #93c5fd !important;
            }


            /* =========================
               SELL disabled note
               ========================= */

            .sell-disabled-note {
                font-size: 0.8rem;
                font-style: italic;
                opacity: 0.72;
                margin-top: -0.35rem;
                line-height: 1.2;
            }


            /* =========================
            Mobile trade controls density

            BUY / SELL are forced into one row only inside:
            with st.container(key="buy_sell_row"):
                ...
            ========================= */

            .st-key-buy_sell_row [data-testid="stLayoutWrapper"] > [data-testid="stElementContainer"] {
                flex: 1 1 50% !important;
                min-width: 0 !important;
                width: 50% !important;
            }

            .st-key-buy_sell_row [data-testid="stLayoutWrapper"] > [data-testid="stElementContainer"] button {
                width: 100% !important;
            }

            /* ===== MOBILE: btns size ===== */
            @media (max-width: 768px) {
                .st-key-trade_actions button {
                    min-height: 44px !important;
                    font-size: 0.9rem !important;
                }

                .st-key-trade_actions .sell-disabled-note {
                    font-size: 0.75rem !important;
                    margin-top: -0.15rem !important;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


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

def _render_trade_panel(bus, clock, account) -> None:
    st.subheader("Trade")

    session_finished = st.session_state.get("session_finished", False)
    sell_disabled = account.shares <= 0 or session_finished

    with st.container(key="trade_actions"):

        # Row 1: BUY + SELL only
        with st.container(key="buy_sell_row"):
            st.button(
                "BUY",
                type="primary",
                key="buy_button",
                disabled=session_finished,
                use_container_width=True,
            )
            if st.session_state.get("buy_button"):
                _open_trade_review(clock, TradeSide.BUY, "BUY")
                st.rerun()

            st.button(
                "SELL",
                key="sell_button",
                disabled=sell_disabled,
                use_container_width=True,
            )
            if st.session_state.get("sell_button"):
                _open_trade_review(clock, TradeSide.SELL, "SELL")
                st.rerun()

        # Row 2: Finish Session separately
        if st.button(
            "Finish Session",
            width="stretch",
            key="finish_session_button",
        ):
            result = bus.publish(
                MarketClosedEvent(timestamp=now_utc()),
                publisher="ui.trading.finish_session",
            )

            st.session_state.session_result = result
            st.session_state.auto_play = False
            st.session_state.session_finished = True
            st.session_state.page = "session_result"

            st.rerun()

        # Row 3: Auto Play
        st.session_state.auto_play = st.toggle(
            "Auto Play",
            value=st.session_state.auto_play,
            key="auto_play_toggle",
        )

        # Row 4: SELL note
        sell_note_placeholder = st.empty()

        if sell_disabled:
            if session_finished:
                sell_note_placeholder.markdown(
                    '<div class="sell-disabled-note">Session is finished.</div>',
                    unsafe_allow_html=True,
                )
            else:
                sell_note_placeholder.markdown(
                    '<div class="sell-disabled-note">SELL is disabled because you do not hold shares.</div>',
                    unsafe_allow_html=True,
                )
        else:
            sell_note_placeholder.markdown(
                '<div class="sell-disabled-note">&nbsp;</div>',
                unsafe_allow_html=True,
            )
def _render_transactions(account) -> None:
    trades = account.trades

    logger.info(
        "RENDER_TRANSACTIONS | trades_count=%s | trades=%s",
        len(trades),
        [
            {
                "side": trade.side.value if hasattr(trade.side, "value") else str(trade.side),
                "qty": trade.quantity,
                "price": trade.price,
                "timestamp": _format_timestamp(trade.timestamp),
            }
            for trade in trades
        ],
    )

    st.divider()
    st.subheader("Transactions")

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

    st.divider()

    _render_trade_panel(bus, clock, account)

    _render_trade_review_dialog_if_needed(bus, account, market)

    _render_transactions(account)

    _rerun_for_autoplay_if_needed(clock)

