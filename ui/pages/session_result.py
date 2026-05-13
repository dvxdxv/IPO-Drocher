import streamlit as st


def _format_money(value: float) -> str:
    return f"${value:,.2f}"


def _format_signed_money(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}${value:,.2f}"


def render_session_result_page() -> None:
    result = st.session_state.get("session_result")

    if not result:
        st.warning("No session result found.")
        if st.button("Back to start"):
            st.session_state.page = "init"
            st.rerun()
        return

    final_equity = result.get("final_equity", 0.0)
    total_pnl = result.get("total_pnl", 0.0)
    realized_pnl = result.get("realized_pnl", 0.0)
    unrealized_pnl = result.get("unrealized_pnl", 0.0)
    roi_percent = result.get("roi_percent", 0.0)
    grade = result.get("grade", "-")
    win_rate = result.get("win_rate", 0.0)
    total_trades = result.get("total_trades", 0)

    st.title("Session Result")
    st.caption("IPO Drocher trading replay completed")

    with st.container(border=True):
        st.markdown(f"## Grade: `{grade}`")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Final Equity", _format_money(final_equity))

        with col2:
            st.metric("Total P&L", _format_signed_money(total_pnl))

        with col3:
            st.metric("ROI", f"{roi_percent:+.2f}%")

        st.divider()

        col4, col5, col6 = st.columns(3)

        with col4:
            st.metric("Realized P&L", _format_signed_money(realized_pnl))

        with col5:
            st.metric("Unrealized P&L", _format_signed_money(unrealized_pnl))

        with col6:
            st.metric("Win Rate", f"{win_rate:.1f}%")

        st.markdown(f"**Total Trades:** {total_trades}")

    st.write("")

    col_restart, col_review = st.columns([1, 1])

    with col_restart:
        if st.button("Start New Session", type="primary", width="stretch"):
            _reset_session_for_new_start()
            st.rerun()

    with col_review:
        if st.button("Review Trading Screen", width="stretch"):
            st.session_state.page = "trading"
            st.rerun()


def _reset_session_for_new_start() -> None:
    keys_to_clear = [
        "engine",
        "session_result",
        "session_finished",
        "trade_review_open",
        "pending_side",
        "pending_label",
        "trade_review_qty",
        "trade_review_qty_buy",
        "trade_review_qty_sell",
        "resume_after_trade_review",
        "trade_toast",
        "auto_play",
        "last_auto_tick_ts",
    ]

    for key in keys_to_clear:
        st.session_state.pop(key, None)

    st.session_state.page = "init"