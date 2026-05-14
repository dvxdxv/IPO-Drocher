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

    pnl_color = "#22c55e" if total_pnl >= 0 else "#ef4444"
    rpnl_color = "#22c55e" if realized_pnl >= 0 else "#ef4444"
    upnl_color = "#22c55e" if unrealized_pnl >= 0 else "#ef4444"

    def signed(v): return f"+${v:,.2f}" if v >= 0 else f"-${abs(v):,.2f}"

    st.markdown(f"""
<style>
.sr-grade {{ font-size:2.8rem; font-weight:900; margin-bottom:4px; }}
.sr-caption {{ font-size:0.9rem; opacity:0.6; margin-bottom:16px; }}
.sr-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin:12px 0; }}
.sr-cell {{ background:rgba(255,255,255,0.04); border-radius:10px; padding:12px 16px; }}
.sr-label {{ font-size:0.8rem; opacity:0.6; margin-bottom:4px; text-transform:uppercase; letter-spacing:0.04em; }}
.sr-value {{ font-size:1.3rem; font-weight:800; }}
</style>

<div class="sr-grade">Grade: {grade}</div>
<div class="sr-caption">IPO Drocher trading replay completed</div>

<div class="sr-grid">
    <div class="sr-cell">
        <div class="sr-label">Final Equity</div>
        <div class="sr-value">${final_equity:,.2f}</div>
    </div>
    <div class="sr-cell">
        <div class="sr-label">Total P&L</div>
        <div class="sr-value" style="color:{pnl_color}">{signed(total_pnl)}</div>
    </div>
    <div class="sr-cell">
        <div class="sr-label">ROI</div>
        <div class="sr-value" style="color:{pnl_color}">{roi_percent:+.2f}%</div>
    </div>
    <div class="sr-cell">
        <div class="sr-label">Win Rate</div>
        <div class="sr-value">{win_rate:.1f}%</div>
    </div>
    <div class="sr-cell">
        <div class="sr-label">Realized P&L</div>
        <div class="sr-value" style="color:{rpnl_color}">{signed(realized_pnl)}</div>
    </div>
    <div class="sr-cell">
        <div class="sr-label">Unrealized P&L</div>
        <div class="sr-value" style="color:{upnl_color}">{signed(unrealized_pnl)}</div>
    </div>
    <div class="sr-cell" style="grid-column:1/-1;">
        <div class="sr-label">Total Trades</div>
        <div class="sr-value">{total_trades}</div>
    </div>
</div>
""", unsafe_allow_html=True)

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