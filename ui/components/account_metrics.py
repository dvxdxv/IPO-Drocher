import streamlit as st


def render_account_metrics(account, price: float) -> dict:
    """
    Render key account metrics.

    Returns calculated values that can be reused by the page:
    - equity
    - unrealized_pnl
    - total_pnl
    """

    equity = account.get_equity(price)
    unrealized_pnl = account.get_unrealized_pnl(price)
    total_pnl = account.realized_pnl + unrealized_pnl

    metric_cols = st.columns(4)

    with metric_cols[0]:
        st.metric("Cash", f"${account.cash:,.2f}")

    with metric_cols[1]:
        st.metric("Shares", f"{account.shares}")

    with metric_cols[2]:
        st.metric("Equity", f"${equity:,.2f}")

    with metric_cols[3]:
        st.metric("Total P&L", f"${total_pnl:,.2f}")

    return {
        "equity": equity,
        "unrealized_pnl": unrealized_pnl,
        "total_pnl": total_pnl,
    }